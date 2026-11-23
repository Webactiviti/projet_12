from dataclasses import dataclass

@dataclass
class SessionConfig :
    temp_dir : str    
    temp_dir_topomap : str 
    temp_dir_img : str 
    temp_dir_data : str 
    db_path : str 
    xdf_file : str 
    temp_rapport : str
    temp_session_id  : str
    name_session : str
