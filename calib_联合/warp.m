% 创建输出文件夹
if ~exist('Outputs/flir', 'dir')
    mkdir('Outputs/flir');
end
if ~exist('Outputs/event', 'dir')
    mkdir('Outputs/event');
end
if ~exist('Outputs/overlay', 'dir')
    mkdir('Outputs/overlay');
end

% 加载相机参数
load('stereo_camera_parameters.mat');

% 创建相机参数对象
cam1 = cameraParameters('IntrinsicMatrix', stereo_params.K1', ...
                       'RadialDistortion', stereo_params.RadialDistortion1, ...
                       'TangentialDistortion', stereo_params.TangentialDistortion1);
                   
cam2 = cameraParameters('IntrinsicMatrix', stereo_params.K2', ...
                       'RadialDistortion', stereo_params.RadialDistortion2, ...
                       'TangentialDistortion', stereo_params.TangentialDistortion2);

% 获取所有图像文件
flirFiles = dir('inputs/flir/*.png');
eventFiles = dir('inputs/event/*.png');

% 确保图像对数量匹配
numImages = min(length(flirFiles), length(eventFiles));

% 处理每对图像
for i = 1:numImages
    % 读取图像对
    I1 = imread(fullfile(flirFiles(i).folder, flirFiles(i).name));  % flir
    I2 = imread(fullfile(eventFiles(i).folder, eventFiles(i).name));  % event
    
    % 去畸变
    I1_undist = undistortImage(I1, cam1);
    I2_undist = undistortImage(I2, cam2);
    
    % 创建输出图像（与event相机同样大小）
    if size(I2, 3) == 3
        O = zeros(size(I2), 'like', I2);  % RGB图像
    else
        O = zeros(size(I2), 'like', I2);  % 灰度图像
    end
    
    % 设置投影平面
    Z = 0;
    
    % 投影变换
    fprintf('处理图像对 %d/%d\n', i, numImages);
    for y = 1:size(I2,1)
        for x = 1:size(I2,2)
            % 从event相机的图像坐标反投影到3D
            X = inv([stereo_params.Rcam(:,1:2) [-1*x;-1*y;-1]]) * ...
                (-Z*stereo_params.Rcam(:,3)-stereo_params.Rcam(:,4));
            
            % 投影到flir相机
            P = stereo_params.Lcam * [X(1);X(2);Z;1];
            P = fix(P/P(end));
            
            % 如果投影点在flir图像范围内，复制像素值
            if P(1)>0 && P(2)>0 && P(1)<=size(I1,2) && P(2)<=size(I1,1)
                if size(I1, 3) == 3
                    O(y,x,1) = I1(P(2),P(1),1);  % R通道
                    O(y,x,2) = I1(P(2),P(1),2);  % G通道
                    O(y,x,3) = I1(P(2),P(1),3);  % B通道
                else
                    O(y,x) = I1(P(2),P(1));  % 灰度图像
                end
            end
        end
    end
    
    % 获取文件名（不包含扩展名）
    [~, name] = fileparts(flirFiles(i).name);
    
    % 保存变换后的FLIR图像
    imwrite(uint8(O), fullfile('Outputs/flir', sprintf('flir_transformed_%s.png', name)));
    
    % 保存EVENT图像
    imwrite(I2, fullfile('Outputs/event', sprintf('event_%s.png', name)));
    
    % 创建并保存重叠图像
    overlay = imshowpair(I2, uint8(O), 'falsecolor', 'ColorChannels', 'red-cyan');
    % 获取当前图像数据
    frame = getframe(gca);
    overlay_img = frame.cdata;
    % 保存重叠图像
    imwrite(overlay_img, fullfile('Outputs/overlay', sprintf('overlay_%s.png', name)));
    close;  % 关闭当前图像窗口
    %{
    // % 可选：显示第一对图像的结果
    // if i == 1
    //     figure;
    //     subplot(2,2,1); imshow(I1); title('Original FLIR');
    //     subplot(2,2,2); imshow(I2); title('Original Event');
    //     subplot(2,2,3); imshow(uint8(O)); title('Transformed FLIR');
    //     subplot(2,2,4); imshowpair(I2,uint8(O),'falsecolor','ColorChannels','red-cyan');
    //     title('Overlay');
    // end
    %}
end

fprintf('处理完成！结果已保存到 Outputs 文件夹下的子文件夹中：\n');
fprintf('- flir: 变换后的FLIR图像\n');
fprintf('- event: EVENT图像\n');
fprintf('- overlay: 重叠效果图像\n');
