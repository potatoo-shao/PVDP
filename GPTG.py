import numpy as np
import pandas as pd
import datetime
import math
import twd97
import json
import geojson
import warnings
import requests
import time

## Might need to download twd97 and geojson
### download through pip3 install 'lib_name'


class GPTG:
    def __init__(self, avg_v, r, theta, start_point, start_vec, distance_cal_with_roadnet=False, check_boundary=False):
        """the class is created for randomly generating trajectories on the map

        Args:
            avg_v (float [m/s]): average speed of vehicle 
            r (float, > 0): maximum radius for choosing next point
            theta (float, radian, > 0): the angle of the pie for choosing next point
            start_point ([[float, float]... [float, float]]): start points list or single start point
            start_vec ([[float, float]... [float, float]]): start directions list or single start vector
            distance_cal_with_roadnet (bool, optional): check and project the new-generated point on the road network. Defaults to False.
            check_boundary (bool, optional): check if the new-generated point is in the valid area or not. Defaults to False.
        """
        self.Data = []
        self.df = None
        self.Avg_Speed = avg_v
        self.Radius = r
        self.Theta = theta
        self.Domain = 'default'
        self.Start_Vec = start_vec
        self.NetCheck = distance_cal_with_roadnet
        self.BoundCheck = check_boundary
        self.Start_Point = []
        self.multiStart = isinstance(start_point[0], list)
        # self.Start_Point = start_point
        if self.multiStart:
            for i in range(len(start_point)):
                self.Start_Point.append(list(twd97.fromwgs84(start_point[i][1], start_point[i][0])))
        else:
            self.Start_Point = list(twd97.fromwgs84(start_point[1], start_point[0]))
            
    def DataToDf(self):
        traj_id = []
        traj_duration = []
        traj_dist = []
        traj_size = []
        point_id = []
        point_lon = []
        point_lat = []
        point_timestamp = []
        point_timedelta = []
        
        for i in range(len(self.Data)):
                for j in range(len(self.Data[i].Locations)):
                    traj_id.append(i)
                    traj_duration.append(self.Data[i].Total_Time)
                    traj_dist.append(self.Data[i].Total_Distance)
                    traj_size.append(self.Data[i].Total_Size)
                    point_id.append(j)
                    point_lon.append(self.Data[i].Locations[j].Coordinates[0])
                    point_lat.append(self.Data[i].Locations[j].Coordinates[1])
                    point_timestamp.append(self.Data[i].Locations[j].Datetime)
                    point_timedelta.append((self.Data[i].Locations[j].Datetime - self.Data[i].Locations[0].Datetime).total_seconds())
                    
        self.df = pd.DataFrame({'traj_id': traj_id, 'traj_duration': traj_duration, 'traj_dist': traj_dist, 'traj_size': traj_size,\
            'point_id': point_id, 'lon': point_lon, 'lat': point_lat, 'timestamp':point_timestamp, 'timedelta': point_timedelta})

        
            
        
    def single_create_trajectory_by_time(self, time, start_time):
        """ create a trajectory(-ies) which travels certain amount of time

        Args:
            time (float): traveling time, the output trajectory will travel greater or equal to time
        """
        cur_traj = self.Trajectory(self.Start_Point, self.Start_Vec, start_time)
        cur_traj.time_based_gen(time, self.Avg_Speed, self.Radius, self.Theta, self.NetCheck, self.BoundCheck)
        self.Data.append(cur_traj)
        
    def single_create_trajecory_by_count(self, count, start_time):
        """ create a trajectory(-ies) which contain certain amount of tracking points

        Args:
            count (int): number of tracking points
        """
        cur_traj = self.Trajectory(self.Start_Point, self.Start_Vec, start_time)
        cur_traj.count_based_gen(count, self.Avg_Speed, self.Radius, self.Theta, self.NetCheck, self.BoundCheck)
        self.Data.append(cur_traj)
    
    def multiStart_create_trajectory_by_time(self, time, start_time):
        """ create a trajectory(-ies) which travels certain amount of time

        Args:
            time (float): traveling time, the output trajectory will travel greater or equal to time
        """
        for i in range(len(self.Start_Point)):
            if isinstance(start_time, list):
                cur_traj = self.Trajectory(self.Start_Point[i], self.Start_Vec[i], start_time[i])
            else:
                cur_traj = self.Trajectory(self.Start_Point[i], self.Start_Vec[i], start_time)
            if isinstance(time, list):
                print("current duration: " + str(time[i]))
                cur_traj.time_based_gen(time[i], self.Avg_Speed, self.Radius, self.Theta, self.NetCheck, self.BoundCheck)
            else:
                cur_traj.time_based_gen(time, self.Avg_Speed, self.Radius, self.Theta, self.NetCheck, self.BoundCheck)
            self.Data.append(cur_traj)
            print("traj " + str(i) + " completed")
        
    def multiStart_create_trajecory_by_count(self, count, start_time):
        """ create a trajectory(-ies) which contain certain amount of tracking points

        Args:
            count (int): number of tracking points
        """
        for i in range(len(self.Start_Point)):
            if isinstance(start_time, list):
                cur_traj = self.Trajectory(self.Start_Point[i], self.Start_Vec[i], start_time[i])
            else:
                cur_traj = self.Trajectory(self.Start_Point[i], self.Start_Vec[i], start_time)
            if isinstance(count, list):
                cur_traj.count_based_gen(count[i], self.Avg_Speed, self.Radius, self.Theta, self.NetCheck, self.BoundCheck)
            else:
                cur_traj.count_based_gen(count, self.Avg_Speed, self.Radius, self.Theta, self.NetCheck, self.BoundCheck)
            self.Data.append(cur_traj)
            print("traj " + str(i) + " completed")
            
    def create_trajectory_by_time(self, time, start_time=datetime.datetime(2022,1,1,0,0,0)):
        if self.multiStart:
            self.multiStart_create_trajectory_by_time(time, start_time)
        else:
            self.single_create_trajectory_by_time(time, start_time)
            
        self.DataToDf()
            
    def create_trajectory_by_count(self, count, start_time=datetime.datetime(2022,1,1,0,0,0)):
        if self.multiStart:
            self.multiStart_create_trajecory_by_count(count, start_time)
        else:
            self.single_create_trajecory_by_count(count, start_time)
            
        self.DataToDf()
            
    def output_csv(self, name=None):
        str_name = ""
        if name == None:
            str_name = 'random_gen_traj_'+ datetime.datetime.now().strftime("%m%d%Y")+'.csv'
        else:
            str_name = name
        
        self.df.to_csv(str_name, index=False)
                    
    def output_json(self, name=None):
        str_name = ""
        if name == None:
            str_name = 'random_gen_traj_'+ datetime.datetime.now().strftime("%m%d%Y")+'.json'
        else:
            str_name = name
            
        self.df.to_json(str_name)
        
        
    def output_geojson(self, name=None):
        str_name = ""
        if name == None:
            str_name = 'random_gen_traj_'+ datetime.datetime.now().strftime("%m%d%Y")
        else:
            str_name = name
        for i in range(len(self.Data)):
            _geojson = {"traj_id": i, "traj_geojson": {"type": "FeatureCollection", "traj_feature":{"Total_TIme": self.Data[i].Total_Time, "Total_Distance": self.Data[i].Total_Distance, "Total_Size": self.Data[i].Total_Size}, "features":[]}}
            for j in range(len(self.Data[i].Locations)):
                feature = {"type": "Feature", "geometry": {"type": "Point", "coordinates": self.Data[i].Locations[j].Coordinates, "properties": {"time": self.Data[i].Locations[j].Datetime.strftime("%Y-%m%dT%H:M:%M")}}}
                _geojson['traj_geojson']['features'].append(feature)
            
            with open(str_name + '_' + str(i) + '.geojson', 'w') as f:
                geojson.dump(_geojson, f)
                
    def output(self,name=None, format='json'):
        """[summary]

        Args:
            name (str, optional): path of the output file. Defaults to None.
            format (str, optional): format of output file. Defaults to 'json'.
        """
        if format == 'csv':
            self.output_csv(name)
        elif format == 'json':
            self.output_json(name)
        elif format == 'geojson':
            self.output_geojson(name)
        else:
            warnings.simplefilter('error', UserWarning)
            warnings.warn("unsupported format")
    
    class Trajectory:
        
        def __init__(self, start_point, start_vec, start_time):
            self.Total_Time = 0
            self.Total_Distance = 0
            self.Total_Size = 1
            self.Last_Point = start_point
            self.Cur_Point = start_point
            self.Cur_Vec = start_vec
            self.Start_Time = start_time
            
            # init Locations array with starting point
            init_point = self.Points()
            init_point.Coordinates = list(twd97.towgs84(start_point[0], start_point[1]))
            temp = init_point.Coordinates[0]
            init_point.Coordinates[0] = init_point.Coordinates[1]
            init_point.Coordinates[1] = temp
            init_point.Direction = start_vec
            init_point.Datetime = start_time
            self.Locations = [init_point]
            
        def time_based_gen(self, time, avg_v, r, theta, network_check, boundary_check):
            while(self.Total_Time < time):
                next_point = self.Points()
                dist = next_point.point_generation(r, theta, self.Cur_Point, self.Cur_Vec)
                
                #TODO  ## The related connection from functions to class are written. un-comment the code and replace the function to enable it
                if boundary_check:
                    parameters = {'x_97': next_point.Coordinates[0], 'y_97': next_point.Coordinates[1]}
                    response = requests.get('http://192.168.50.118/ds_api/checkPointInOperationArea', params=parameters)
                    parse = json.loads(response.read())
                    valid = parse['result']['contains']
                    while(~valid):
                        self.Cur_Vec = np.multiply(self.Cur_Vec, -1)
                        dist = next_point.point_generation(r, theta, self.Cur_Point, self.Cur_Vec)
                        parameters = {'x_97': next_point.Coordinates[0], 'y_97': next_point.Coordinates[1]}
                        response = requests.get('http://192.168.50.118/ds_api/checkPointInOperationArea', params=parameters)
                        parse = json.loads(response.read())
                        valid = parse['result']['contains']
                        
                if network_check:
                    print("project current generated point on road network. Not Implemented") # comment out when function implemented
                    # new_coordinate = network_check()
                    # next_point.Coordinate = new_coordinate
                    # dist = ShortestPathDistance(new_coordinate, self.Cur_Point)
                    # err_count = 1
                    # while dist > r:
                    #     next_point.point_generation(r, theta, self.Cur_Point, self.Cur_Vec)
                    #     new_coordinate = network_check()
                    #     next_point.Coordinate = new_coordinate
                    #     dist = ShortestPathDistance(new_coordinate, self.Cur_Point)
                    #     err_count += 1
                    #     if err_count > 30:
                    #         warnings.simplefilter('error', UserWarning)
                    #         warnings.warn('The generator could not escape from projecting the other road.\n Please check if the roads are too closed or increase the radius.')
                            
                
                # update trajectory info
                self.Total_Time += dist/avg_v
                self.Total_Distance += dist
                self.Total_Size += 1
                
                # update next point info
                next_point.Datetime = self.Locations[-1].Datetime + datetime.timedelta(seconds=dist/avg_v)
                self.Last_Point = self.Cur_Point
                self.Cur_Point = next_point.Coordinates
                next_point.Coordinates = list(twd97.towgs84(next_point.Coordinates[0], next_point.Coordinates[1]))
                temp = next_point.Coordinates[0]
                next_point.Coordinates[0] = next_point.Coordinates[1]
                next_point.Coordinates[1] = temp
                
                # update vector
                self.Cur_Vec = [m - n for m, n in zip(self.Cur_Point, self.Last_Point)]
                next_point.Direction = self.Cur_Vec
                # vec_len = np.sqrt(self.Cur_Vec[0]**2 + self.Cur_Vec[1]**2)
                # self.Cur_Vec = [i/vec_len for i in self.Cur_Vec]
                
                # update point
                self.Locations.append(next_point)
                
            
        def count_based_gen(self, count, avg_v, r, theta, network_check, boundary_check):
            for i in range(count-1):
                next_point = self.Points()
                dist = next_point.point_generation(r, theta, self.Cur_Point, self.Cur_Vec)
                
                # TODO ## The related connection from functions to class are written. un-comment the code and replace the function to enable it
                if boundary_check:
                    time.sleep(0.5)
                    header ={'content-type': 'application/json', 'User-Agent': 'My User Agent 1.0', 'From': 'youremail@domain.com'}
                    parameters = {'x_97': next_point.Coordinates[0], 'y_97': next_point.Coordinates[1]}
                    response = requests.post('http://192.168.50.118/ds_api/checkPointInOperationArea', headers=header, data=json.dumps(parameters))
                    parse = response.json()
                    valid = parse['result'][0]['contains']
                    while(valid != True):
                        self.Cur_Vec = np.multiply(self.Cur_Vec, -1)
                        dist = next_point.point_generation(r, theta, self.Cur_Point, self.Cur_Vec)
                        parameters = {'x_97': next_point.Coordinates[0], 'y_97': next_point.Coordinates[1]}
                        response = requests.post('http://192.168.50.118/ds_api/checkPointInOperationArea', headers=header, data=json.dumps(parameters))
                        parse = response.json()
                        valid = parse['result'][0]['contains']
                        
                if network_check:
                    print("project current generated point on road network. Not Implemented") # comment out when function implemented
                    # new_coordinate = network_check()
                    # next_point.Coordinate = new_coordinate
                    # dist = ShortestPathDistance(new_coordinate, self.Cur_Point)
                    # err_count = 1
                    # while dist > r:
                    #     next_point.point_generation(r, theta, self.Cur_Point, self.Cur_Vec)
                    #     new_coordinate = network_check()
                    #     next_point.Coordinate = new_coordinate
                    #     dist = ShortestPathDistance(new_coordinate, self.Cur_Point)
                    #     err_count += 1
                    #     if err_count > 30:
                    #         warnings.simplefilter('error', UserWarning)
                    #         warnings.warn('The generator could not escape from projecting the other road.\n Please check if the roads are too closed or increase the radius.')
                
                # update trajectory info
                self.Total_Time += dist/avg_v
                self.Total_Distance += dist
                self.Total_Size += 1
                
                # update next point info
                next_point.Datetime = self.Locations[-1].Datetime + datetime.timedelta(seconds=dist/avg_v)
                self.Last_Point = self.Cur_Point
                self.Cur_Point = next_point.Coordinates
                next_point.Coordinates = list(twd97.towgs84(next_point.Coordinates[0], next_point.Coordinates[1]))
                temp = next_point.Coordinates[0]
                next_point.Coordinates[0] = next_point.Coordinates[1]
                next_point.Coordinates[1] = temp
                
                # update vector
                self.Cur_Vec = [m - n for m, n in zip(self.Cur_Point, self.Last_Point)]
                next_point.Direction = self.Cur_Vec
                # vec_len = np.sqrt(self.Cur_Vec[0]**2 + self.Cur_Vec[1]**2)
                # self.Cur_Vec = [i/vec_len for i in self.Cur_Vec]
                self.Locations.append(next_point)
                
        class Points:
            
            def __init__(self):
                self.Coordinates = []
                self.Direction = []
                self.Datetime = datetime.datetime(2022,1,1,0,0,0) # current start time is always the same. it can be changed afterwards if needed
                
            def point_generation(self, r, theta, start_point, start_vec):
                chosen_r = np.random.uniform(0, r) + 1e-6
                chosen_theta = np.random.uniform(-theta, theta)
                slope = start_vec[1]/start_vec[0]
                cur_angle = math.atan2(start_vec[1], start_vec[0])
                new_angle = cur_angle + chosen_theta + 1e-6
                self.Coordinates = [start_point[0] + chosen_r*math.cos(new_angle), start_point[1] + chosen_r*math.sin(new_angle)]
                return chosen_r
                
        