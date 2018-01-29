# coding=utf-8

from datetime import datetime

import transitfeed

from osm2gtfs.creators.trips_creator import TripsCreator
from osm2gtfs.core.helper import Helper
from osm2gtfs.core.elements import Line, Itinerary


class TripsCreatorAlpizar(TripsCreator):

    def add_trips_to_feed(self, feed, data):

        lines = data.get_routes()

        # line (osm route master | gtfs route)
        for line_id, line in lines.iteritems():
            # debug
            print("DEBUG. procesando la linea:", line.name)

            # itinerary (osm route | non existent gtfs element)
            itineraries = line.get_itineraries()
            for itinerary in itineraries:
                # debug
                print("DEBUG. procesando el itinerario", itinerary.name)

                # shape for itinerary
                shape_id = self._add_shape_to_feed(feed, itinerary.osm_id, itinerary)

                # Luego moverlo a un método "add_trips_by_frequency"
                for itinerary_schedule in data.schedule["itinerario"][line_id]:
                    operation = itinerary_schedule["operacion"].encode('utf-8')
                    service_period = self._create_service_period(feed, operation)
                    route = feed.GetRoute(line_id)

                    trip = route.AddTrip(feed, headsign=itinerary.name,
                                         service_period=service_period)
                    # add empty attributes to make navitia happy
                    trip.block_id = ""
                    trip.wheelchair_accessible = ""
                    trip.bikes_allowed = ""
                    trip.shape_id = shape_id
                    trip.direction_id = ""

                    # add stop_times and frequency
                    for f_start, f_end, f_min in itinerary_schedule["frequencies"]:
                        # read departure time from json schedule
                        start_time = datetime.strptime(f_start, "%H:%M")
                        start_time = str(start_time.time())

                        # calculate last arrival time for GTFS
                        start_sec = transitfeed.TimeToSecondsSinceMidnight(start_time)
                        duration_sec = start_sec + (int(itinerary.tags['duration']) * 60)
                        trip_end_time = transitfeed.FormatSecondsSinceMidnight(duration_sec)

                        self.add_trip_stops(feed, trip, itinerary, start_time, trip_end_time)
                        Helper.interpolate_stop_times(trip)

                        # add frequency
                        end_time = datetime.strptime(f_end, "%H:%M")
                        end_time = str(end_time.time())
                        headway_secs = int(f_min) * 60
                        trip.AddFrequency(start_time, end_time, headway_secs)

        return

    def _create_service_period(self, feed, operation):
        try:
            service = feed.GetServicePeriod(operation)
            if service is not None:
                return service
        except KeyError:
            print("INFO. No existe el service_period para la operación:",
                  operation, " por lo que será creado")

        if operation == "weekday":
            service = transitfeed.ServicePeriod("weekday")
            service.SetWeekdayService(True)
            service.SetWeekendService(False)
        elif operation == "saturday":
            service = transitfeed.ServicePeriod("saturday")
            service.SetWeekdayService(False)
            service.SetWeekendService(False)
            service.SetDayOfWeekHasService(5, True)
        elif operation == "sunday":
            service = transitfeed.ServicePeriod("sunday")
            service.SetWeekdayService(False)
            service.SetWeekendService(False)
            service.SetDayOfWeekHasService(6, True)
        else:
            raise KeyError("uknown operation keyword")

        service.SetStartDate(self.config['feed_info']['start_date'])
        service.SetEndDate(self.config['feed_info']['end_date'])
        feed.AddServicePeriodObject(service)
        return feed.GetServicePeriod(operation)

    @staticmethod
    def add_trip_stops(feed, trip, route, start_time, end_time):
        '''
        This method was copy and pasted from fenix trips creator
        note: variable route actually is an itinierary (route variant)
        '''
        if isinstance(route, Itinerary):
            i = 1
            for stop in route.stops:
                if i == 1:
                    # timepoint="1" (Times are considered exact)
                    trip.AddStopTime(feed.GetStop(str(stop.stop_id)), stop_time=start_time)
                elif i == len(route.stops):
                    # timepoint="0" (Times are considered approximate)
                    trip.AddStopTime(feed.GetStop(str(stop.stop_id)), stop_time=end_time)
                else:
                    # timepoint="0" (Times are considered approximate)
                    trip.AddStopTime(feed.GetStop(str(stop.stop_id)))
                i += 1
