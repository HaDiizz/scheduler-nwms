import models
import os
from dotenv import load_dotenv
import httpx
import datetime
import requests
from helpers.utils import cal_min_down, cal_sla
from helpers.api import service_list
from bson.objectid import ObjectId


load_dotenv()


url = 'https://notify-api.line.me/api/notify'
line_noti_token = os.environ['LINE_NOTI_TOKEN']
headers = {'content-type': 'application/x-www-form-urlencoded',
           'Authorization': 'Bearer ' + line_noti_token}




def service_down_handler():
    now = datetime.datetime.now()
    month = now.month
    year = now.year
    
    print("service_down_handler is running...")
    
    try:
        response = service_list("ALL")
        if not response or response is None:
            response = []
        service = models.Service.objects(month=month, year=year).first()

        if not service :
            if response :
                get_service_all(response, month, year)
        
        else :
            response = service_list("DOWN")
            if response :
                service_in_db = []
                service_now = []
                get_service_down(response, month, year, service_in_db, service_now)

        if response:
            return "Saved Successfully"
        else:
            return []
    except Exception as ex:
        print("service_down_handler error: ", ex)
        return None


def get_service_all(response, month, year) :

    for item in response:
                state = item['extensions']['state']
                service_id = item['id']
                service_name = item['title']
                groups = []
                
                for group_item in item['extensions']['groups']:
                    groups.append(group_item)

                if state == 2:
                    service = models.Service.objects(
                        service_id=service_id, month=month, year=year).first()
                    if service:
                        service_list_ids = service.service_list
                        if not service_list_ids:
                            new_service_list = models.ServiceList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_service_list.save()
                            service.service_list.append(new_service_list)
                            count_down = service.count + 1
                            service.count = count_down
                            service.save()
                            

                        last_service_list_id = service_list_ids[-1]
                        service_list = models.ServiceList.objects(
                            id=last_service_list_id.id, 
                            last_state=-1).first()

                        if not service_list:
                            new_service_list = models.ServiceList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_service_list.save()

                            service.service_list.append(new_service_list)
                            count_down = service.count + 1
                            service.count = count_down
                            service.save()

                        else :
                            time_down = service_list.last_time_down
                            unix_timestamp = int(time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)

                            if minute >= 1440 :
                                if service_list.last_state == -1:
                                    service_list.last_state = -2
                                    service_list.minutes = minute
                                    service_list.save()

                                    if len(service_list_ids) > 0:
                                        service_all_ids = []
                                        for item_id in service_list_ids:
                                            if isinstance(item_id, ObjectId):
                                                service_all_ids.append(item_id.id)
                                            else:
                                                service_all_ids.append(ObjectId(item_id.id))
                                        query = models.ServiceList.objects(id__in=service_all_ids)
                                        matching_data = query.all()
                                        sum_min = 0
                                        for data in matching_data:
                                            sum_min += data.minutes
                                        sla = float(cal_sla(month, year, sum_min))
                                        service.availability = sla
                                        service.save()
                    else:
                        new_service_list = models.ServiceList(
                            state=int(state),
                            last_state=-1,
                            remark="",
                            last_time_up=datetime.datetime.now(),
                            last_time_down=datetime.datetime.now(),
                            minutes=0,
                        )
                        new_service_list.save()

                        new_service = models.Service(
                            service_id=service_id,
                            name=service_name,
                            month=month,
                            year=year,
                            count=1,
                            availability=100,
                            service_list=[
                                new_service_list.id,
                            ],
                        )
                        new_service.save()
                elif state == 0:
                    service = models.Service.objects(
                        service_id=service_id, month=month, year=year).first()
                    if service:
                        service_list_ids = service.service_list
                        if not service_list_ids:
                            continue
                        last_service_list_id = service_list_ids[-1]

                        service_list = models.ServiceList.objects(
                            id=last_service_list_id.id, last_state=-1).first()
                        
                        if not service_list :
                            service_list = models.ServiceList.objects(
                            id=last_service_list_id.id, last_state=-2).first()

                        if service_list:
                            last_time_down = service_list.last_time_down
                            unix_timestamp = int(last_time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)
                            service_list.last_state = 0
                            service_list.minutes = minute
                            service_list.save()

                        if service_list:
                            service = models.Service.objects(
                                service_id=service_id, month=month, year=year).first()
                            service_list_ids = []
                            sum_min = 0

                            for value in service.service_list:
                                service_list_ids.append(value.id)

                            if len(service_list_ids) > 0:
                                service_all_ids = []
                                for item_id in service_list_ids:
                                    if isinstance(item_id, ObjectId):
                                        service_all_ids.append(item_id.id)
                                    else:
                                        service_all_ids.append(ObjectId(item_id.id))
                                query = models.ServiceList.objects(id__in=service_all_ids)
                                matching_data = query.all()

                                for data in matching_data:
                                    sum_min += data.minutes
                                sla = float(cal_sla(month, year, sum_min))
                                service.availability = sla
                                service.save()
                    else:
                        new_service = models.Service(
                            service_id=service_id,
                            name=service_name,
                            month=month,
                            year=year,
                            count=0,
                            availability=100,
                            groups=groups
                        )
                        new_service.save()


def get_service_down(response, month, year, servicedown_in_db, servicedown_now) :
    
    for item in response:
                state = item['extensions']['state']
                service_id = item['id']
                service_name = item['title']
                groups = []

                servicedown = models.ServiceDown.objects(
                        service_id=service_id).first()
                
                if servicedown :
                    
                    servicedown_now.append(service_id)

                else :

                    new_servicedown = models.ServiceDown(
                                service_id = service_id,
                                last_time_down=datetime.datetime.now()
                            )

                    new_servicedown.save()
                    servicedown_now.append(service_id)
                
                service = models.Service.objects(
                        service_id=service_id, month=month, year=year).first()
                
                if service:
                        last_id = []
                        service_list_ids = service.service_list
                        

                        if not service_list_ids:
                            new_service_list = models.ServiceList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )
                            
                            new_service_list.save()
                            service.service_list.append(new_service_list)
                            count_down = service.count + 1
                            service.count = count_down
                            service.save()
                            
                            
                            time = datetime.datetime.now()
                            format_time = time.strftime('%Y-%m-%d %H:%M')
                            msg = "🔴" + "\nService : " + service_id + "\nState : " + \
                                "Down" + "\nTime Down : " + format_time
                            r = requests.post(
                                url, headers=headers, data={'message': msg})
                            
                        last_service_list_id = service_list_ids[-1]
                        service_list = models.ServiceList.objects(
                            id=last_service_list_id.id, 
                            last_state=-1).first()

                        if not service_list:
                            
                            new_service_list = models.ServiceList(
                                state=int(state),
                                last_state=-1,
                                remark="",
                                last_time_up=datetime.datetime.now(),
                                last_time_down=datetime.datetime.now(),
                                minutes=0,
                            )

                            new_service_list.save()

                            service.service_list.append(new_service_list)
                            count_down = service.count + 1
                            service.count = count_down
                            service.save()

                            time = datetime.datetime.now()
                            format_time = time.strftime('%Y-%m-%d %H:%M')
                            msg = "🔴" + "\nService : " + service_id + "\nState : " + \
                                "Down" + "\nTime Down : " + format_time
                            r = requests.post(
                                url, headers=headers, data={'message': msg})
                            
                        else :
                            
                            time_down = service_list.last_time_down
                            unix_timestamp = int(time_down.timestamp())
                            minute = cal_min_down(unix_timestamp)

                            if minute >= 1440 :
                                if service_list.last_state == -1:
                                    service_list.last_state = -2
                                    service_list.minutes = minute
                                    service_list.save()

                                    if len(service_list_ids) > 0:
                                        service_all_ids = []
                                        for item_id in service_list_ids:
                                            if isinstance(item_id, ObjectId):
                                                service_all_ids.append(item_id.id)
                                            else:
                                                service_all_ids.append(ObjectId(item_id.id))
                                        query = models.ServiceList.objects(id__in=service_all_ids)
                                        matching_data = query.all()
                                        sum_min = 0
                                        for data in matching_data:
                                            sum_min += data.minutes
                                        sla = float(cal_sla(month, year, sum_min))
                                        service.availability = sla
                                        service.save()
                else:
                    new_service_list = models.ServiceList(
                        state=int(state),
                        last_state=-1,
                        remark="",
                        last_time_up=datetime.datetime.now(),
                        last_time_down=datetime.datetime.now(),
                        minutes=0,
                    )
                    new_service_list.save()

                    new_service = models.Service(
                        service_id=service_id,
                        name=service_name,
                        month=month,
                        year=year,
                        count=1,
                        availability=100,
                        service_list=[
                            new_service_list.id,
                        ],
                    )
                    new_service.save()

                    time = datetime.datetime.now()
                    format_time = time.strftime('%Y-%m-%d %H:%M')
                    msg = "🔴" + "\nService : " + service_id + "\nState : " + \
                        "Down" + "\nTime Down : " + format_time
                    r = requests.post(
                        url, headers=headers, data={'message': msg})

    all_service = models.ServiceDown.objects.all()   
    for service in all_service :
        servicedown_in_db.append(service.service_id)
    
    filter_service_down = [service for service in servicedown_in_db if service not in servicedown_now]
    
    for service_id in filter_service_down :

        service = models.Service.objects(
                            service_id=service_id, month=month, year=year).first()
        if service:
            
            service_list_ids = service.service_list
            last_service_list_id = service_list_ids[-1]

            service_list = models.ServiceList.objects(
                id=last_service_list_id.id, last_state=-1).first()
            
            if not service_list :
                service_list = models.ServiceList.objects(
                id=last_service_list_id.id, last_state=-2).first()

            if service_list:
                last_time_down = service_list.last_time_down
                unix_timestamp = int(last_time_down.timestamp())
                minute = cal_min_down(unix_timestamp)
                service_list.last_state = 0
                service_list.minutes = minute
                service_list.save()

            if service_list:
                service = models.Service.objects(
                    service_id=service_id, month=month, year=year).first()
                service_list_ids = []
                sum_min = 0

                for value in service.service_list:
                    service_list_ids.append(value.id)

                if len(service_list_ids) > 0:
                    service_all_ids = []
                    for item_id in service_list_ids:
                        if isinstance(item_id, ObjectId):
                            service_all_ids.append(item_id)
                        else:
                            service_all_ids.append(ObjectId(item_id))
                    query = models.ServiceList.objects(id__in=service_all_ids)
                    matching_data = query.all()

                    for data in matching_data:
                        sum_min += data.minutes
                    sla = float(cal_sla(month, year, sum_min))
                    service.availability = sla
                    service.save()
        else:
            new_service = models.Service(
                service_id=service_id,
                name=service_name,
                month=month,
                year=year,
                count=0,
                availability=100,
                groups=groups
            )
            new_service.save()
    
    models.ServiceDown.objects(service_id__in=filter_service_down).delete()

