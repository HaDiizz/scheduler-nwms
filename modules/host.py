import models
import os
from dotenv import load_dotenv
import httpx
import datetime
import requests
from helpers.utils import cal_min_down, cal_sla, DEFAULT_LAT, DEFAULT_LNG
from helpers.api import host_is_down, API_URL, HEADERS
from bson.objectid import ObjectId

load_dotenv()


url = 'https://notify-api.line.me/api/notify'
line_noti_token = os.environ['LINE_NOTI_TOKEN']
headers = {'content-type': 'application/x-www-form-urlencoded',
           'Authorization': 'Bearer ' + line_noti_token}




def host_down_handler():
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    
    print("host_down_handler is running...")

    try:
        with httpx.Client() as client:
            params = {
                "columns": ['name', 'state', 'last_state', 'labels', 'groups', 'address'],
            }
            response = client.get(
                f"{API_URL}/domain-types/host/collections/all",
                headers=HEADERS,
                params=params
            )
            
            if response.status_code == 200:
                response = response.json()
                if response:
                    response = response['value']
            else:
                response = []
        host = models.Host.objects(month=month, year=year).first()
        
        if not host :
            if response :
                get_host_all(response, month, year)
        
        else :
            response = host_is_down()
            if response :
                hostdown_in_db = []
                hostdown_now = []
                get_host_down(response, month, year, hostdown_in_db, hostdown_now)

        if response:
            return "Saved Successfully"
        else:
            return []
    except Exception as ex:
        print("host_down_handler error: ", ex)
        return None


def get_host_all(response, month, year) :

    for item in response:
                ip_address = item['extensions']['address']
                state = item['extensions']['state']
                host_id = item['id']
                host_name = item['title']
                groups = []
                
                for group_item in item['extensions']['groups']:
                    groups.append(group_item)

                if state == 1:
                    host = models.Host.objects(
                        host_id=host_id, month=month, year=year).first()
                    if host:
                        host_list_ids = host.host_list
                        if not host_list_ids:
                            new_host_list = models.HostList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_host_list.save()
                            host.host_list.append(new_host_list)
                            count_down = host.count + 1
                            host.count = count_down
                            host.save()
                            

                        last_host_list_id = host_list_ids[-1]
                        host_list = models.HostList.objects(
                            id=last_host_list_id.id, 
                            last_state=-1).first()

                        if not host_list:
                            new_host_list = models.HostList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_host_list.save()

                            host.host_list.append(new_host_list)
                            count_down = host.count + 1
                            host.count = count_down
                            host.save()

                        else :
                            time_down = host_list.last_time_down
                            unix_timestamp = int(time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)

                            if minute >= 1440 :
                                if host_list.last_state == -1:
                                    host_list.last_state = -2
                                    host_list.minutes = minute
                                    host_list.save()

                                    if len(host_list_ids) > 0:
                                        host_all_ids = []
                                        for item_id in host_list_ids:
                                            if isinstance(item_id, ObjectId):
                                                host_all_ids.append(item_id.id)
                                            else:
                                                host_all_ids.append(ObjectId(item_id.id))
                                        query = models.HostList.objects(id__in=host_all_ids)
                                        matching_data = query.all()
                                        sum_min = 0
                                        for data in matching_data:
                                            sum_min += data.minutes
                                        sla = float(cal_sla(month, year, sum_min))
                                        host.availability = sla
                                        host.save()
                    else:
                        new_host_list = models.HostList(
                            state=int(state),
                            last_state=-1,
                            remark="",
                            last_time_up=datetime.datetime.now(),
                            last_time_down=datetime.datetime.now(),
                            minutes=0,
                        )
                        new_host_list.save()

                        new_host = models.Host(
                            host_id=host_id,
                            name=host_name,
                            ip_address=ip_address,
                            month=month,
                            year=year,
                            count=1,
                            availability=100,
                            coordinates=(DEFAULT_LAT, DEFAULT_LNG),
                            floor="",
                            room="",
                            host_list=[
                                new_host_list.id,
                            ],
                        )
                        new_host.save()
                elif state == 0:
                    host = models.Host.objects(
                        host_id=host_id, month=month, year=year).first()
                    if host:
                        host_list_ids = host.host_list
                        if not host_list_ids:
                            continue
                        last_host_list_id = host_list_ids[-1]

                        host_list = models.HostList.objects(
                            id=last_host_list_id.id, last_state=-1).first()
                        
                        if not host_list :
                            host_list = models.HostList.objects(
                            id=last_host_list_id.id, last_state=-2).first()

                        if host_list:
                            last_time_down = host_list.last_time_down
                            unix_timestamp = int(last_time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)
                            host_list.last_state = 0
                            host_list.minutes = minute
                            host_list.save()

                        if host_list:
                            host = models.Host.objects(
                                host_id=host_id, month=month, year=year).first()
                            host_list_ids = []
                            sum_min = 0

                            for value in host.host_list:
                                host_list_ids.append(value.id)

                            if len(host_list_ids) > 0:
                                host_all_ids = []
                                for item_id in host_list_ids:
                                    if isinstance(item_id, ObjectId):
                                        host_all_ids.append(item_id.id)
                                    else:
                                        host_all_ids.append(ObjectId(item_id.id))
                                query = models.HostList.objects(id__in=host_all_ids)
                                matching_data = query.all()

                                for data in matching_data:
                                    sum_min += data.minutes
                                sla = float(cal_sla(month, year, sum_min))
                                host.availability = sla
                                host.save()
                    else:
                        new_host = models.Host(
                            host_id=host_id,
                            name=host_name,
                            ip_address=ip_address,
                            month=month,
                            year=year,
                            count=0,
                            availability=100,
                            coordinates=(DEFAULT_LAT, DEFAULT_LNG),
                            floor="",
                            room="",
                            groups=groups
                        )
                        new_host.save()


def get_host_down(response, month, year, hostdown_in_db, hostdown_now) :
    
    for item in response:
                ip_address = item['extensions']['address']
                state = item['extensions']['state']
                host_id = item['id']
                host_name = item['title']
                groups = []

                hostdown = models.HostDown.objects(
                        host_id=host_id).first()
                
                if hostdown :
                    
                    hostdown_now.append(host_id)

                else :

                    new_hostdown = models.HostDown(
                                host_id = host_id,
                                last_time_down=datetime.datetime.now()
                            )

                    new_hostdown.save()
                    hostdown_now.append(host_id)
                
                host = models.Host.objects(
                        host_id=host_id, month=month, year=year).first()
                
                if host:
                        last_id = []
                        host_list_ids = host.host_list
                        

                        if not host_list_ids:
                            new_host_list = models.HostList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )
                            
                            new_host_list.save()
                            host.host_list.append(new_host_list)
                            count_down = host.count + 1
                            host.count = count_down
                            host.save()
                            
                            
                            time = datetime.datetime.now()
                            format_time = time.strftime('%Y-%m-%d %H:%M')
                            msg = "🔴" + "\nHost : " + host_id + "\nState : " + \
                                "Down" + "\nTime Down : " + format_time
                            r = requests.post(
                                url, headers=headers, data={'message': msg})
                            
                        last_host_list_id = host_list_ids[-1]
                        host_list = models.HostList.objects(
                            id=last_host_list_id.id, 
                            last_state=-1).first()

                        if not host_list:
                            
                            new_host_list = models.HostList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_host_list.save()

                            host.host_list.append(new_host_list)
                            count_down = host.count + 1
                            host.count = count_down
                            host.save()

                            time = datetime.datetime.now()
                            format_time = time.strftime('%Y-%m-%d %H:%M')
                            msg = "🔴" + "\nHost : " + host_id + "\nState : " + \
                                "Down" + "\nTime Down : " + format_time
                            r = requests.post(
                                url, headers=headers, data={'message': msg})
                            
                        else :
                            
                            time_down = host_list.last_time_down
                            unix_timestamp = int(time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)

                            if minute >= 1440 :
                                if host_list.last_state == -1:
                                    host_list.last_state = -2
                                    host_list.minutes = minute
                                    host_list.save()

                                    if len(host_list_ids) > 0:
                                        host_all_ids = []
                                        for item_id in host_list_ids:
                                            if isinstance(item_id, ObjectId):
                                                host_all_ids.append(item_id.id)
                                            else:
                                                host_all_ids.append(ObjectId(item_id.id))
                                        query = models.HostList.objects(id__in=host_all_ids)
                                        matching_data = query.all()
                                        sum_min = 0
                                        for data in matching_data:
                                            sum_min += data.minutes
                                        sla = float(cal_sla(month, year, sum_min))
                                        host.availability = sla
                                        host.save()
                else:
                    new_host_list = models.HostList(
                        state=int(state),
                        last_state=-1,
                        remark="",
                        last_time_up=datetime.datetime.now(),
                        last_time_down=datetime.datetime.now(),
                        minutes=0,
                    )
                    new_host_list.save()

                    new_host = models.Host(
                        host_id=host_id,
                        name=host_name,
                        ip_address=ip_address,
                        month=month,
                        year=year,
                        count=1,
                        availability=100,
                        coordinates=(DEFAULT_LAT, DEFAULT_LNG),
                        floor="",
                        room="",
                        host_list=[
                            new_host_list.id,
                        ],
                    )
                    new_host.save()

                    time = datetime.datetime.now()
                    format_time = time.strftime('%Y-%m-%d %H:%M')
                    msg = "🔴" + "\nHost : " + host_id + "\nState : " + \
                        "Down" + "\nTime Down : " + format_time
                    r = requests.post(
                        url, headers=headers, data={'message': msg})

    all_host = models.HostDown.objects.all()   
    for host in all_host :
        hostdown_in_db.append(host.host_id)
    
    filter_host_down = [host for host in hostdown_in_db if host not in hostdown_now]
    

    for host_id in filter_host_down :

        host = models.Host.objects(
                            host_id=host_id, month=month, year=year).first()
        if host:

            host_list_ids = host.host_list
            last_host_list_id = host_list_ids[-1]

            host_list = models.HostList.objects(
                id=last_host_list_id.id, last_state=-1).first()
            
            if not host_list :
                host_list = models.HostList.objects(
                id=last_host_list_id.id, last_state=-2).first()

            if host_list:
                last_time_down = host_list.last_time_down
                unix_timestamp = int(last_time_down.timestamp())
                minute = cal_min_down(unix_timestamp)
                host_list.last_state = 0
                host_list.minutes = minute
                host_list.save()

            if host_list:
                host = models.Host.objects(
                    host_id=host_id, month=month, year=year).first()
                host_list_ids = []
                sum_min = 0

                for value in host.host_list:
                    host_list_ids.append(value.id)

                if len(host_list_ids) > 0:
                    host_all_ids = []
                    for item_id in host_list_ids:
                        if isinstance(item_id, ObjectId):
                            host_all_ids.append(item_id)
                        else:
                            host_all_ids.append(ObjectId(item_id))
                    query = models.HostList.objects(id__in=host_all_ids)
                    matching_data = query.all()

                    for data in matching_data:
                        sum_min += data.minutes
                    sla = float(cal_sla(month, year, sum_min))
                    host.availability = sla
                    host.save()
        else:
            new_host = models.Host(
                host_id=host_id,
                name=host_name,
                ip_address=ip_address,
                month=month,
                year=year,
                count=0,
                availability=100,
                groups=groups
            )
            new_host.save()

    models.HostDown.objects(host_id__in=filter_host_down).delete()

