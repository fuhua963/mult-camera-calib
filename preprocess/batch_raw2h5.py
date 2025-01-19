import os
from metavision_core.event_io import EventsIterator
import h5py
import numpy as np
from tqdm import tqdm

def convert_raw_to_h5(raw_path, h5_path, x_offset=340, y_offset=60):
    """将单个raw文件转换为h5文件，并应用坐标偏移
    
    Args:
        raw_path: raw文件路径
        h5_path: 输出的h5文件路径
        x_offset: x方向的偏移量
        y_offset: y方向的偏移量
    """
    print(f"处理文件: {raw_path}")
    
    # 预先计算大致的事件数量
    estimated_events = int(60 * 1e6)  # 60秒 * 每秒100万个事件
    
    # 预分配numpy数组，使用正确的数据类型
    x_array = np.zeros(estimated_events, dtype=np.uint16)
    y_array = np.zeros(estimated_events, dtype=np.uint16)
    p_array = np.zeros(estimated_events, dtype=np.uint8)
    t_array = np.zeros(estimated_events, dtype=np.int64)
    
    current_idx = 0
    
    mv_iterator = EventsIterator(input_path=raw_path, delta_t=1000000, start_ts=0,
                               max_duration=1e6 * 60)
    total_steps = int((1e6 * 60) // 1000000)

    for evs in tqdm(mv_iterator, total=total_steps, desc="读取事件"):
        batch_events = len(evs)
        
        if current_idx + batch_events > len(x_array):
            new_size = len(x_array) + estimated_events
            x_array.resize(new_size, refcheck=False)
            y_array.resize(new_size, refcheck=False)
            p_array.resize(new_size, refcheck=False)
            t_array.resize(new_size, refcheck=False)
        
        # 应用坐标偏移，并确保结果为非负数
        x_coords = evs['x'] - x_offset
        y_coords = evs['y'] - y_offset
        
        
        # 转换数据类型并保存
        x_array[current_idx:current_idx+batch_events] = x_coords.astype(np.uint16)
        y_array[current_idx:current_idx+batch_events] = y_coords.astype(np.uint16)
        p_array[current_idx:current_idx+batch_events] = evs['p'].astype(np.uint8)
        t_array[current_idx:current_idx+batch_events] = evs['t']
        
        current_idx += batch_events

    # 裁剪到实际大小
    x_array = x_array[:current_idx]
    y_array = y_array[:current_idx]
    p_array = p_array[:current_idx]
    t_array = t_array[:current_idx]

    # 保存到HDF5文件
    with h5py.File(h5_path, 'w') as f:
        f.create_dataset('x', data=x_array, compression='gzip', compression_opts=1)
        f.create_dataset('y', data=y_array, compression='gzip', compression_opts=1)
        f.create_dataset('p', data=p_array, compression='gzip', compression_opts=1)
        f.create_dataset('t', data=t_array, compression='gzip', compression_opts=1)
    
    print(f"已保存到: {h5_path}")
    print(f"事件总数: {current_idx}")

def batch_convert(base_input_dir, base_output_dir, x_offset=340, y_offset=60):
    """批量转换文件夹下的所有raw文件
    
    Args:
        base_input_dir: 输入目录路径
        base_output_dir: 输出目录路径
        x_offset: x方向的偏移量
        y_offset: y方向的偏移量
    """
    os.makedirs(base_output_dir, exist_ok=True)
    
    # 处理1.10和1.11两个文件夹
    for folder in ['1.10', '1.11']:
        output_folder = os.path.join(base_output_dir, folder)
        os.makedirs(output_folder, exist_ok=True)
        
        input_base = os.path.join(base_input_dir, folder)
        # 遍历子文件夹（1,2,3...）
        subfolders = [f for f in os.listdir(input_base) if os.path.isdir(os.path.join(input_base, f))]
        subfolders.sort(key=int)  # 确保按数字顺序排序
        
        for i, subfolder in enumerate(subfolders, 1):
            event_folder = os.path.join(input_base, subfolder, 'event')
            if not os.path.exists(event_folder):
                print(f"跳过 {event_folder} - 文件夹不存在")
                continue
                
            # 查找event.raw文件
            raw_file = os.path.join(event_folder, 'event.raw')
            if not os.path.exists(raw_file):
                print(f"跳过 {raw_file} - 文件不存在")
                continue
            
            h5_path = os.path.join(output_folder, f"{i}.h5")
            convert_raw_to_h5(raw_file, h5_path, x_offset, y_offset)

if __name__ == '__main__':
    # 设置输入和输出的基础路径
    base_input_dir = ""  # 请修改为你的raw文件所在的基础路径
    base_output_dir = "./h5data"   # 请修改为你想要保存h5文件的基础路径
    
    # 设置坐标偏移量
    x_offset = 340  # x方向的偏移
    y_offset = 60   # y方向的偏移
    
    batch_convert(base_input_dir, base_output_dir, x_offset, y_offset) 