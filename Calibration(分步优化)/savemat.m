% 假设 cameraParams 是已有的 cameraParameters 对象

% 提取内参矩阵和径向畸变系数
intrinsicMatrix1 = cameraParams1.Intrinsics.IntrinsicMatrix;
radialDistortion1 = cameraParams1.RadialDistortion;

% 可选：提取更多参数（如切向畸变、图像尺寸等）
tangentialDistortion1 = cameraParams1.TangentialDistortion;
imageSize1 = cameraParams1.ImageSize;

% 将提取的数据保存到 .mat 文件中
save('camera_intrinsics1.mat', 'intrinsicMatrix1', 'radialDistortion1', ...
    'tangentialDistortion1', 'imageSize1');

% 输出确认信息
disp('内参数据已成功保存到 camera_intrinsics.mat 文件中。');