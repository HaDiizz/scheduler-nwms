import models
import os
from dotenv import load_dotenv
import httpx
import datetime
import requests
from helpers.utils import cal_min_down, cal_sla, get_all_ap_list
from helpers.api import access_point_list, access_point_is_down
from bson.objectid import ObjectId


load_dotenv()


url = 'https://notify-api.line.me/api/notify'
line_noti_token = os.environ['LINE_NOTI_TOKEN']
headers = {'content-type': 'application/x-www-form-urlencoded',
           'Authorization': 'Bearer ' + line_noti_token}


def accessPoint_down_handler():
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    
    print("accessPoint_down_handler is running...")

    try:
        get_ap_data = access_point_list()
        response = get_all_ap_list(get_ap_data)
        accessPoint = models.AccessPoint.objects(month=month, year=year).first()
        if not accessPoint or accessPoint is None :
            if response :
                get_accessPoint_all(response, month, year)
        
        else :
            ap_data_list = []
            get_ap_data = access_point_is_down()
            for item in get_ap_data:
                if item["extensions"]["description"].startswith("AP"):
                    host_name =  item["extensions"]["host_name"]
                    state = int(item["extensions"]["state"])
                    if host_name == "WLC":
                        ap_data_list.append({
                            "id": host_name,
                            "extensions": {
                                "services_with_info":[
                                    [ item["extensions"]["description"], state, '', f"Accesspoint: online" ]
                                ]
                            }
                        })
                    else:
                        group_suffix = item['extensions'].get('description')[-3:]
                        if group_suffix[-1] == 'A':
                            group_prefix = item['extensions'].get('description')[:-2]
                        else:
                            group_prefix = item['extensions'].get('description')[:-3]

                        ap_data_list.append({
                            "id": host_name,
                            "extensions": {
                                "services_with_info": [
                                    [
                                        item["extensions"]["description"],
                                        state,
                                        '',
                                        f"Status: up, Group: { 'Dorm10' if group_prefix == 'DRM10' else 'Dorm11' if group_prefix == 'DRM11' else 'Dorm12' if group_prefix == 'DRM12' else 'Dorm13' if group_prefix == 'DRM13' else 'Dorm14' if group_prefix == 'DRM14' else 'Dorm15' if group_prefix == 'DRM15' else 'Dorm1' if group_prefix == 'DRM1' else 'default'}"
                                    ]
                                ]
                            }
                        })
            response = get_all_ap_list(ap_data_list)
            if response :
                accessPoint_in_db = []
                accessPoint_now = []
                get_accessPoint_down(response, month, year, accessPoint_in_db, accessPoint_now)

        if response:
            return "Saved Successfully"
        else:
            return []
    except Exception as ex:
        print("AccessPoint error: ", ex)
        return None


def get_accessPoint_all(response, month, year) :

    for item in response:
                accessPoint_id = item['accessPoint_id']
                state = item['state']
                lat = item['lat']
                lng = item['lng']
                accessPoint_name = item['name']
                group = item['group']

                if state == 2:
                    accessPoint = models.AccessPoint.objects(
                        accessPoint_id=accessPoint_id, month=month, year=year).first()
                    if accessPoint:
                        accessPoint_list_ids = accessPoint.accessPoint_list
                        if not accessPoint_list_ids:
                            new_accessPoint_list = models.AccessPointList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_accessPoint_list.save()
                            accessPoint.accessPoint_list.append(new_accessPoint_list)
                            count_down = accessPoint.count + 1
                            accessPoint.count = count_down
                            accessPoint.save()
                            

                        last_accessPoint_list_id = accessPoint_list_ids[-1]
                        accessPoint_list = models.AccessPointList.objects(
                            id=last_accessPoint_list_id.id, 
                            last_state=-1).first()

                        if not accessPoint_list:
                            new_accessPoint_list = models.AccessPointList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_accessPoint_list.save()

                            accessPoint.accessPoint_list.append(new_accessPoint_list)
                            count_down = accessPoint.count + 1
                            accessPoint.count = count_down
                            accessPoint.save()

                        else :
                            time_down = accessPoint_list.last_time_down
                            unix_timestamp = int(time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)

                            if minute >= 1440 :
                                if accessPoint_list.last_state == -1:
                                    accessPoint_list.last_state = -2
                                    accessPoint_list.minutes = minute
                                    accessPoint_list.save()

                                    if len(accessPoint_list_ids) > 0:
                                        accessPoint_all_ids = []
                                        for item_id in accessPoint_list_ids:
                                            if isinstance(item_id, ObjectId):
                                                accessPoint_all_ids.append(item_id.id)
                                            else:
                                                accessPoint_all_ids.append(ObjectId(item_id.id))
                                        query = models.AccessPointList.objects(id__in=accessPoint_all_ids)
                                        matching_data = query.all()
                                        sum_min = 0

                                        for data in matching_data:
                                            sum_min += data.minutes
                                        sla = float(cal_sla(month, year, sum_min))
                                        accessPoint.availability = sla
                                        accessPoint.save()
                    else:
                        new_accessPoint_list = models.AccessPointList(
                            state=int(state),
                            last_state=-1,
                            remark="",
                            last_time_up=datetime.datetime.now(),
                            last_time_down=datetime.datetime.now(),
                            minutes=0,
                        )
                        new_accessPoint_list.save()

                        new_accessPoint = models.AccessPoint(
                            accessPoint_id=accessPoint_id,
                            name=accessPoint_name,
                            month=month,
                            year=year,
                            count=1,
                            availability=100,
                            coordinates=(lat, lng),
                            group=group,
                            floor="",
                            room="",
                            accessPoint_list=[
                                new_accessPoint_list.id,
                            ],
                        )
                        new_accessPoint.save()
                elif state == 0:
                    accessPoint = models.AccessPoint.objects(
                        accessPoint_id=accessPoint_id, month=month, year=year).first()
                    if accessPoint:
                        accessPoint_list_ids = accessPoint.accessPoint_list
                        if not accessPoint_list_ids:
                            continue
                        last_accessPoint_list_id = accessPoint_list_ids[-1]

                        accessPoint_list = models.AccessPointList.objects(
                            id=last_accessPoint_list_id.id, last_state=-1).first()
                        
                        if not accessPoint_list :
                            accessPoint_list = models.AccessPointList.objects(
                            id=last_accessPoint_list_id.id, last_state=-2).first()

                        if accessPoint_list:
                            last_time_down = accessPoint_list.last_time_down
                            unix_timestamp = int(last_time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)
                            accessPoint_list.last_state = 0
                            accessPoint_list.minutes = minute
                            accessPoint_list.save()

                        if accessPoint_list:
                            accessPoint = models.AccessPoint.objects(
                                accessPoint_id=accessPoint_id, month=month, year=year).first()
                            accessPoint_list_ids = []
                            sum_min = 0

                            for value in accessPoint.accessPoint_list:
                                accessPoint_list_ids.append(value.id)

                            if len(accessPoint_list_ids) > 0:
                                accessPoint_all_ids = []
                                for item_id in accessPoint_list_ids:
                                    if isinstance(item_id, ObjectId):
                                        accessPoint_all_ids.append(item_id.id)
                                    else:
                                        accessPoint_all_ids.append(ObjectId(item_id.id))
                                query = models.AccessPointList.objects(id__in=accessPoint_all_ids)
                                matching_data = query.all()

                                for data in matching_data:
                                    sum_min += data.minutes
                                sla = float(cal_sla(month, year, sum_min))
                                accessPoint.availability = sla
                                accessPoint.save()
                    else:
                        new_accessPoint = models.AccessPoint(
                            accessPoint_id=accessPoint_id,
                            name=accessPoint_name,
                            month=month,
                            year=year,
                            count=0,
                            availability=100,
                            coordinates=(lat, lng),
                            group=group,
                            floor="",
                            room="",
                        )
                        new_accessPoint.save()


def get_accessPoint_down(response, month, year, accessPoint_down_in_db, accessPoint_down_now) :
    
    for item in response:
                accessPoint_id = item['accessPoint_id']
                state = item['state']
                lat = item['lat']
                lng = item['lng']
                accessPoint_name = item['name']
                group = item['group']

                accessPoint_down = models.AccessPointDown.objects(
                        accessPoint_id=accessPoint_id).first()
                
                if accessPoint_down :
                    accessPoint_down_now.append(accessPoint_id)

                else :

                    new_accessPoint_down = models.AccessPointDown(
                                accessPoint_id = accessPoint_id,
                                last_time_down=datetime.datetime.now()
                            )

                    new_accessPoint_down.save()
                    accessPoint_down_now.append(accessPoint_id)
                
                accessPoint = models.AccessPoint.objects(
                        accessPoint_id=accessPoint_id, month=month, year=year).first()
                
                if accessPoint:
                        last_id = []
                        accessPoint_list_ids = accessPoint.accessPoint_list
                        

                        if not accessPoint_list_ids:
                            new_accessPoint_list = models.AccessPointList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )
                            
                            new_accessPoint_list.save()
                            accessPoint.accessPoint_list.append(new_accessPoint_list)
                            count_down = accessPoint.count + 1
                            accessPoint.count = count_down
                            accessPoint.save()
                            
                            
                            time = datetime.datetime.now()
                            format_time = time.strftime('%Y-%m-%d %H:%M')
                            msg = "🔴" + "\nAccessPoint : " + accessPoint_id + "\nState : " + \
                                "Down" + "\nTime Down : " + format_time
                            r = requests.post(
                                url, headers=headers, data={'message': msg})
                            
                        last_accessPoint_list_id = accessPoint_list_ids[-1]
                        accessPoint_list = models.AccessPointList.objects(
                            id=last_accessPoint_list_id.id, 
                            last_state=-1).first()

                        if not accessPoint_list:
                            
                            new_accessPoint_list = models.AccessPointList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_accessPoint_list.save()

                            accessPoint.accessPoint_list.append(new_accessPoint_list)
                            count_down = accessPoint.count + 1
                            accessPoint.count = count_down
                            accessPoint.save()

                            time = datetime.datetime.now()
                            format_time = time.strftime('%Y-%m-%d %H:%M')
                            msg = "🔴" + "\nAccessPoint : " + accessPoint_id + "\nState : " + \
                                "Down" + "\nTime Down : " + format_time
                            r = requests.post(
                                url, headers=headers, data={'message': msg})
                            
                        else :
                            
                            time_down = accessPoint_list.last_time_down
                            unix_timestamp = int(time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)

                            if minute >= 1440 :
                                if accessPoint_list.last_state == -1:
                                    accessPoint_list.last_state = -2
                                    accessPoint_list.minutes = minute
                                    accessPoint_list.save()

                                    if len(accessPoint_list_ids) > 0:
                                        accessPoint_all_ids = []
                                        for item_id in accessPoint_list_ids:
                                            if isinstance(item_id, ObjectId):
                                                accessPoint_all_ids.append(item_id.id)
                                            else:
                                                accessPoint_all_ids.append(ObjectId(item_id.id))
                                        query = models.AccessPointList.objects(id__in=accessPoint_all_ids)
                                        matching_data = query.all()
                                        sum_min = 0
                                        for data in matching_data:
                                            sum_min += data.minutes
                                        sla = float(cal_sla(month, year, sum_min))
                                        accessPoint.availability = sla
                                        accessPoint.save()
                else:
                    new_accessPoint_list = models.AccessPointList(
                        state=int(state),
                        last_state=-1,
                        remark="",
                        last_time_up=datetime.datetime.now(),
                        last_time_down=datetime.datetime.now(),
                        minutes=0,
                    )
                    new_accessPoint_list.save()

                    new_accessPoint = models.AccessPoint(
                        accessPoint_id=accessPoint_id,
                        name=accessPoint_name,
                        month=month,
                        year=year,
                        count=1,
                        availability=100,
                        coordinates=(lat, lng),
                        group=group,
                        floor="",
                        room="",
                        accessPoint_list=[
                            new_accessPoint_list.id,
                        ],
                    )
                    new_accessPoint.save()

                    time = datetime.datetime.now()
                    format_time = time.strftime('%Y-%m-%d %H:%M')
                    msg = "🔴" + "\nAccessPoint : " + accessPoint_id + "\nState : " + \
                        "Down" + "\nTime Down : " + format_time
                    r = requests.post(
                        url, headers=headers, data={'message': msg})

    all_accessPoint = models.AccessPointDown.objects.all()   
    for accessPoint in all_accessPoint :
        accessPoint_down_in_db.append(accessPoint.accessPoint_id)
    
    filter_accessPoint_down = [accessPoint for accessPoint in accessPoint_down_in_db if accessPoint not in accessPoint_down_now]
    
    for accessPoint_id in filter_accessPoint_down :

        accessPoint = models.AccessPoint.objects(
                            accessPoint_id=accessPoint_id, month=month, year=year).first()
        if accessPoint:
            
            accessPoint_list_ids = accessPoint.accessPoint_list
            last_accessPoint_list_id = accessPoint_list_ids[-1]

            accessPoint_list = models.AccessPointList.objects(
                id=last_accessPoint_list_id.id, last_state=-1).first()
            
            if not accessPoint_list :
                accessPoint_list = models.AccessPointList.objects(
                id=last_accessPoint_list_id.id, last_state=-2).first()

            if accessPoint_list:
                last_time_down = accessPoint_list.last_time_down
                unix_timestamp = int(last_time_down.timestamp())
                minute = cal_min_down(unix_timestamp)
                accessPoint_list.last_state = 0
                accessPoint_list.minutes = minute
                accessPoint_list.save()

            if accessPoint_list:
                accessPoint = models.AccessPoint.objects(
                    accessPoint_id=accessPoint_id, month=month, year=year).first()
                accessPoint_list_ids = []
                sum_min = 0

                for value in accessPoint.accessPoint_list:
                    accessPoint_list_ids.append(value.id)

                if len(accessPoint_list_ids) > 0:
                    accessPoint_all_ids = []
                    for item_id in accessPoint_list_ids:
                        if isinstance(item_id, ObjectId):
                            accessPoint_all_ids.append(item_id)
                        else:
                            accessPoint_all_ids.append(ObjectId(item_id))
                    query = models.AccessPointList.objects(id__in=accessPoint_all_ids)
                    matching_data = query.all()

                    for data in matching_data:
                        sum_min += data.minutes
                    sla = float(cal_sla(month, year, sum_min))
                    accessPoint.availability = sla
                    accessPoint.save()
        else:
            new_accessPoint = models.AccessPoint(
                accessPoint_id=accessPoint_id,
                name=accessPoint_name,
                month=month,
                year=year,
                count=0,
                availability=100,
                coordinates=(lat, lng),
                group=group,
                floor="",
                room="",
            )
            new_accessPoint.save()
    
    models.AccessPointDown.objects(accessPoint_id__in=filter_accessPoint_down).delete()
