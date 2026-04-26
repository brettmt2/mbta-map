# format the time display to follow MBTA's guidelines
# https://www.mbta.com/developers/real-time-display-guidelines
# next, implement departure time, headways fields

def realtime_display(now, data):
    for dest in data:
        keep = []
        dest_data = data[dest]

        if len(dest_data) > 0:
            for obj in dest_data:
                if obj and obj['status']:
                    delta = obj['time'] - now
                    if delta.total_seconds() > 0:
                        secs = int(delta.total_seconds())
                        
                        if secs <= 30:
                            time_str = 'ARR'
                        elif secs <= 90 and obj['v_curr_stop'] == obj['stop_id'] and obj['status'] == 'STOPPED_AT':
                            time_str = 'BRD'
                        else:
                            mins = (secs + 30) // 60
                            if mins >= 60:
                                hours = mins // 60
                                remaining_mins = mins % 60
                                time_str = f'{hours} hr {remaining_mins} min'
                            else:
                                time_str = f'{mins} min'
                        obj['time'] = time_str
                        keep.append(obj)
            data[dest] = keep[:5]

    return data
                                        





                    











                    
    #                 if total_seconds < 30:
    #                     time_str = 'ARR'
    #                 elif 0 == 0:

        
                        
                    
    #                 # if total_seconds < 60:
    #                 #     time_obj['time'] = f'{total_seconds} sec'
    #                 # else:
    #                 #     time_obj['time'] = f'{total_seconds // 60} min'

    #     # data[dest] = keep[:5]

    # # return data
