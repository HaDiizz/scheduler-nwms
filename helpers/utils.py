import models
import datetime


DORM_LIST = [
    "Dorm10",
    "Dorm11",
    "Dorm12",
    "Dorm13",
    "Dorm14",
    "Dorm15",
]
DEFAULT_LAT = 7.0088136
DEFAULT_LNG = 100.498062


def cal_sla(month, year, sum_min):
    start_date = datetime.datetime(year, month, 1, 0, 1)
    current_date = datetime.datetime.now()
    time_difference = current_date - start_date
    total_minutes = int(time_difference.total_seconds() / 60)
    sla = ((total_minutes - sum_min)/total_minutes) * 100
    return sla


def cal_min_down(down_time):
    date = datetime.datetime.now()
    current_time = int(date.timestamp())
    time_difference_seconds = current_time - down_time
    time_difference_minute = int(int(time_difference_seconds)/60)
    return time_difference_minute


def location_list():
    return models.Location.objects().order_by("name")


def get_all_ap_list(ap_prop):
    get_ap_list = ap_prop
    if get_ap_list is None:
        get_ap_list = []
    ap_list = []
    location_data = []
    for location in location_list():
        location_data.append({
            "location_id": location.location_id,
            "lat": location.lat,
            "lng": location.lng,
        })
    for data in get_ap_list:
        for item in data["extensions"]["services_with_info"]:
            if item[0].startswith("AP"):
                name = item[0].split()[1]
                state = int(item[1])
                accessPoint_id = data["id"] + ":" + item[0]
                found_location = False
                group_data = None
                query_ap = models.AccessPointLocation.objects(
                    name=name).first()
                for location in location_data:
                    if item[3] and "Group" in item[3]:
                        group_data = item[3].split(", ")[1].split(": ")[1]
                        if group_data == "Dorm10" and location["location_id"] == "DRM10":
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break
                        elif group_data == "Dorm11" and location["location_id"] == "DRM11":
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break
                        elif group_data == "Dorm12" and location["location_id"] == "DRM12":
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break
                        elif group_data == "Dorm13" and location["location_id"] == "DRM13":
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break
                        elif group_data == "Dorm14" and location["location_id"] == "DRM14":
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break
                        elif group_data == "Dorm15" and location["location_id"] == "DRM15":
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break
                        elif name.startswith(location["location_id"]) and group_data not in DORM_LIST:
                            ap_list.append({
                                "accessPoint_id": accessPoint_id,
                                "name": name,
                                "state": state,
                                "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                                "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                                "group": location["location_id"]
                            })
                            found_location = True
                            break

                    if data["id"] == "WLC" and name.startswith(location["location_id"]) and not name.startswith("DRM15") and not location["location_id"].startswith("DRM15"):
                        ap_list.append({
                            "accessPoint_id": accessPoint_id,
                            "name": name,
                            "state": state,
                            "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                            "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                            "group": location["location_id"]
                        })
                        found_location = True
                        break
                    elif data["id"] == "WLC" and name.startswith("DRM15") and location["location_id"].startswith("DRM15"):
                        ap_list.append({
                            "accessPoint_id": accessPoint_id,
                            "name": name,
                            "state": state,
                            "lat": query_ap["coordinates"][0] if query_ap else location["lat"],
                            "lng": query_ap["coordinates"][1] if query_ap else location["lng"],
                            "group": "DRM15"
                        })
                        found_location = True
                        break
                if not found_location:
                    ap_list.append({
                        "accessPoint_id": accessPoint_id,
                        "name": name,
                        "state": state,
                        "lat":  query_ap["coordinates"][0] if query_ap else DEFAULT_LAT,
                        "lng":  query_ap["coordinates"][1] if query_ap else DEFAULT_LNG,
                        "group": ""
                    })
    return ap_list


def get_service_group_monthly_sla(group_id):

    current_datetime = datetime.datetime.now()
    sla = 0
    count = 0

    query = models.Service.objects(
        month=current_datetime.month, year=current_datetime.year)
    matching_data = query.all()

    for service in matching_data:
        group = service.groups

        for group_name in group:
            if group_name == group_id:
                sla += service.availability
                count += 1
                break

    if count > 0:
        return '{:.4f}'.format(round(sla / count, 8))
    else:
        return ""
