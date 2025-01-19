import os
import shutil
from tqdm import tqdm

def natural_sort_key(s):
    """提取文件名中的数字用于排序"""
    import re
    # 提取文件名中的数字部分
    numbers = re.findall(r'\d+', s)
    if numbers:
        return int(numbers[0])
    return 0

def copy_image_pairs(base_dir, output_dir):
    """整理并复制图像对
    
    Args:
        base_dir: 根目录路径
        output_dir: 输出目录路径
    """
    # 创建输出目录结构
    for folder in ['1.10', '1.11']:
        folder_path = os.path.join(output_dir, folder)
        os.makedirs(folder_path, exist_ok=True)
        
        # 获取RGB图像路径和重建图像路径
        rgb_base = os.path.join(base_dir, folder)
        result_base = os.path.join(base_dir, 'results', folder)
        
        # 获取所有子文件夹
        subfolders = [f for f in os.listdir(rgb_base) if os.path.isdir(os.path.join(rgb_base, f))]
        subfolders.sort(key=int)  # 确保按数字顺序排序
        
        print(f"处理 {folder} 文件夹...")
        for i, subfolder in enumerate(tqdm(subfolders), 1):
            # RGB图像路径
            rgb_folder = os.path.join(rgb_base, subfolder, 'Master', 'RGB')
            # 重建图像路径
            recon_folder = os.path.join(result_base, subfolder, 'e2calib')
            
            if not os.path.exists(rgb_folder) or not os.path.exists(recon_folder):
                print(f"跳过 {subfolder} - 文件夹不存在")
                continue
            
            # 获取图像列表并按数字顺序排序
            rgb_images = [f for f in os.listdir(rgb_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
            recon_images = [f for f in os.listdir(recon_folder) if f.endswith(('.png', '.jpg', '.jpeg'))]
            
            rgb_images.sort(key=natural_sort_key)
            recon_images.sort(key=natural_sort_key)
            
            # 创建该组的输出文件夹
            pair_folder = os.path.join(output_dir, folder, str(i))
            rgb_output = os.path.join(pair_folder, 'rgb')
            recon_output = os.path.join(pair_folder, 'event')
            os.makedirs(rgb_output, exist_ok=True)
            os.makedirs(recon_output, exist_ok=True)
            
            # 复制RGB图像
            for j, img in enumerate(rgb_images):
                src = os.path.join(rgb_folder, img)
                dst = os.path.join(rgb_output, f"{j+1}.png")
                shutil.copy2(src, dst)
            
            # 复制重建图像
            for j, img in enumerate(recon_images):
                src = os.path.join(recon_folder, img)
                dst = os.path.join(recon_output, f"{j+1}.png")
                shutil.copy2(src, dst)
            
            print(f"完成 {folder}/{subfolder} - RGB: {len(rgb_images)}张, 重建: {len(recon_images)}张")

if __name__ == '__main__':
    base_dir = "."  # 当前目录
    output_dir = "./image_pairs"  # 输出目录
    
    copy_image_pairs(base_dir, output_dir)
