import arcpy
import math
import sys

if __name__ == '__main__':
    arcpy.ImportToolbox('AGRC Geocode Tools.tbx')
    expected_table = r'Data\TestData.gdb\results'
    fields = ("INID", "INADDR", "INZONE",
              "MatchAddress", "Zone", "Score",
              "XCoord", "YCoord")

    results = arcpy.GeocodeTable(sys.argv[1],
                                 r'Data\TestData.gdb\AddressTable',
                                 'OBJECTID',
                                 'ADDRESS',
                                 'zone',
                                 'Address points and road centerlines (default)',
                                 'NAD 1983 UTM Zone 12N',
                                 r'Data\TestOutput')

    total_rows = 0
    rows_passed = 0
    with arcpy.da.SearchCursor(results, fields) as actual_cursor, \
            arcpy.da.SearchCursor(expected_table, fields) as expected_cursor:
            for expected_row in expected_cursor:
                actual_row = actual_cursor.next()
                total_rows += 1
                failed = False
                actual_row = [s.upper() if type(s) is str else s for s in actual_row]
                act_id, act_inaddr, act_inzone, act_matchaddr, act_zone, act_score, act_x, act_y = actual_row
                expected_row = [s.upper() if type(s) is str else s for s in actual_row]
                exp_id, exp_inaddr, exp_inzone, exp_matchaddr, exp_zone, exp_score, exp_x, exp_y = expected_row

                if act_id != exp_id or \
                   act_inaddr != exp_inaddr or \
                   act_inzone != exp_inzone or \
                   act_matchaddr != exp_matchaddr or \
                   act_zone != exp_zone:
                    failed = True
                elif act_x and exp_x and act_y and exp_y and \
                        math.sqrt((act_x - exp_x) ** 2 + (act_y - exp_y) ** 2) > 1:
                            failed = True

                if failed:
                    print 'Failed:'
                    print 'Actual:', actual_row
                    print 'Expected', expected_row
                else:
                    rows_passed += 1

    print "{} rows passed of {} total_rows".format(rows_passed, total_rows)
