from osm2gtfs.creators.stops_creator import StopsCreator

class StopsCreatorCrGam(StopsCreator):

        def _define_stop_id(self, stop):
            """
            This function returns the GTFS stop id to be used for a stop.
            It can be overridden by custom creators to change how stop_ids are made
            up.

            :return stop_id: A string with the stop_id for use in the GTFS
            """

            #  Use a GTFS stop_id coming from OpenStreetMap data
            if "ref:gtfs" in stop.tags:
                stop_id = stop.tags['ref:gtfs']
            elif "ref" in stop.tags:
                stop_id = stop.tags['ref']

            # Use a GTFS stop_id matching to OpenStreetMap objects
            else:
                stop_id = "OSM:" + stop.osm_type + ":" + str(stop.osm_id)

            return stop_id
