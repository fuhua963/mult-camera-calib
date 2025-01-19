import os
from metavision_core.event_io import RawReader
from tqdm import tqdm

def extract_timestamps(raw_path, txt_path, polarity=0, do_time_shifting=True):
    """从raw文件中提取时间戳并保存到txt文件
    
    Args:
        raw_path: raw文件路径
        txt_path: 保存时间戳的txt文件路径
        polarity: 触发极性，0为正，1为负
        do_time_shifting: 是否进行时间偏移
    """
    print(f"处理文件: {raw_path}")
    
    try:
        with RawReader(str(raw_path), do_time_shifting=do_time_shifting) as ev_data:
            while not ev_data.is_done():
                ev_data.load_n_events(1000000)
            triggers = ev_data.get_ext_trigger_events()
        
        if len(triggers) > 0:
            print(f"总触发信号数量: {len(triggers)}")
            print(f"首个触发: p={triggers['p'][0]}, t={triggers['t'][0]}")
            print(f"末个触发: p={triggers['p'][-1]}, t={triggers['t'][-1]}")

            if polarity in (0, 1):
                triggers = triggers[triggers['p'] == polarity].copy()
            
            # 保存时间戳到txt文件
            os.makedirs(os.path.dirname(txt_path), exist_ok=True)
            with open(txt_path, 'w') as f:
                for i, t in enumerate(triggers['t']):
                    f.write(f"{t}\n")
            
            print(f"已保存时间戳到: {txt_path}")
        else:
            print("未检测到触发信号")
            
    except Exception as e:
        print(f"处理失败: {e}")

def batch_process_timestamps(base_input_dir, base_output_dir, polarity=0, do_time_shifting=False):
    """批量处理文件夹下的所有raw文件的时间戳
    
    Args:
        base_input_dir: 包含1.10和1.11文件夹的根目录
        base_output_dir: 输出目录（h5data）
        polarity: 触发极性
        do_time_shifting: 是否进行时间偏移
    """
    # 处理1.10和1.11两个文件夹
    for folder in ['1.10', '1.11']:
        input_base = os.path.join(base_input_dir, folder)
        output_base = os.path.join(base_output_dir, folder)
        
        if not os.path.exists(input_base):
            print(f"跳过 {input_base} - 文件夹不存在")
            continue
            
        os.makedirs(output_base, exist_ok=True)
            
        # 遍历子文件夹（1,2,3...）
        subfolders = [f for f in os.listdir(input_base) if os.path.isdir(os.path.join(input_base, f))]
        subfolders.sort(key=int)  # 确保按数字顺序排序
        
        for i, subfolder in enumerate(tqdm(subfolders, desc=f"处理 {folder}"), 1):
            event_folder = os.path.join(input_base, subfolder, 'event')
            if not os.path.exists(event_folder):
                print(f"跳过 {event_folder} - 文件夹不存在")
                continue
                
            # 查找event.raw文件
            raw_file = os.path.join(event_folder, 'event.raw')
            if not os.path.exists(raw_file):
                print(f"跳过 {raw_file} - 文件不存在")
                continue
            
            # 设置输出txt文件路径（保存到h5data目录）
            txt_file = os.path.join(output_base, f"{i}.txt")
            extract_timestamps(raw_file, txt_file, polarity, do_time_shifting)

if __name__ == '__main__':
    # 设置输入和输出目录路径
    base_input_dir = ""  # 请修改为你的数据所在的基础路径
    base_output_dir = "./h5data"  # 输出到h5data目录
    
    # 批量处理时间戳
    batch_process_timestamps(base_input_dir, base_output_dir, polarity=0, do_time_shifting=False)
