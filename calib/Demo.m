%% Written by Muhammet Balcilar, France, muhammetbalcilar@gmail.com
% All rights reserved
%%%%%%%%%%%%

clear all
close all

% 动态获取event和flir文件夹下的所有png文件
eventFiles = dir('inputs/event/*.png');
flirFiles = dir('inputs/flir/*.png');

% 提取文件名中的数字并排序
[~, eventOrder] = sort(str2double(regexp({eventFiles.name}, '\d+', 'match', 'once')));
[~, flirOrder] = sort(str2double(regexp({flirFiles.name}, '\d+', 'match', 'once')));

% 重新排序文件列表
eventFiles = eventFiles(eventOrder);
flirFiles = flirFiles(flirOrder);

eventFiles = eventFiles(1:20);
flirFiles = flirFiles(1:20);

% 构建完整的文件路径
file1 = fullfile({flirFiles.folder}, {flirFiles.name});
file2 = fullfile({eventFiles.folder}, {eventFiles.name});

% 明确指定棋盘格大小
boardSize = [7, 9]; % 行数和列数

% Detect checkerboards in images
[imagePoints{1}, boardSize1, imagesUsed1] = detectCheckerboardPoints(file1);
[imagePoints{2}, boardSize2, imagesUsed2] = detectCheckerboardPoints(file2);

% 显示检测结果统计
disp(['FLIR相机成功检测数量: ' num2str(sum(imagesUsed1))]);
disp(['Event相机成功检测数量: ' num2str(sum(imagesUsed2))]);
disp(['两相机都成功检测的数量: ' num2str(sum(imagesUsed1 & imagesUsed2))]);

% 显示检测失败的图像编号
disp('FLIR相机检测失败的图像:');
disp(find(~imagesUsed1));
disp('Event相机检测失败的图像:');
disp(find(~imagesUsed2));

% 验证检测到的棋盘格大小是否符合预期
if ~isequal(boardSize1, boardSize) || ~isequal(boardSize2, boardSize)
    warning('检测到的棋盘格大小与预期不符');
    disp(['检测到的大小: ' num2str(boardSize1) ' 和 ' num2str(boardSize2)]);
    disp(['预期大小: ' num2str(boardSize)]);
end

% 确保commonValidIdx的长度与检测结果匹配
commonValidIdx = imagesUsed1 & imagesUsed2;
if length(commonValidIdx) > size(imagePoints{1}, 3)
    commonValidIdx = commonValidIdx(1:size(imagePoints{1}, 3));
end

% 只保留两个相机都成功检测到棋盘格的图像
imagePoints{1} = imagePoints{1}(:,:,commonValidIdx);
imagePoints{2} = imagePoints{2}(:,:,commonValidIdx);
file1 = file1(commonValidIdx);
file2 = file2(commonValidIdx);

% 检查imagePoints中是否存在无效值
disp('检查imagePoints中的无效值：');
disp(['Camera 1 NaN数量: ' num2str(sum(isnan(imagePoints{1}(:))))]);
disp(['Camera 2 NaN数量: ' num2str(sum(isnan(imagePoints{2}(:))))]);
disp(['Camera 1 Inf数量: ' num2str(sum(isinf(imagePoints{1}(:))))]);
disp(['Camera 2 Inf数量: ' num2str(sum(isinf(imagePoints{2}(:))))]);

% 如果存在无效值，移除包含无效值的图像对
validPoints = all(isfinite(imagePoints{1}), [1,2]) & all(isfinite(imagePoints{2}), [1,2]);
if ~all(validPoints)
    disp(['移除 ' num2str(sum(~validPoints)) ' 对包含无效值的图像']);
    imagePoints{1} = imagePoints{1}(:,:,validPoints);
    imagePoints{2} = imagePoints{2}(:,:,validPoints);
    file1 = file1(validPoints);
    file2 = file2(validPoints);
end

% 检查是否有足够的有效图像对
if size(imagePoints{1}, 3) < 3
    error('需要至少3对有效的棋盘格图像进行标定');
end

disp(['最终使用的有效图像对数量: ' num2str(size(imagePoints{1}, 3))]);

% Generate world coordinates of the checkerboards keypoints
squareSize = 100;  % in units of 'mm'
worldPoints = generateCheckerboardPoints(boardSize, squareSize);


[param, pairsUsed, estimationErrors] = my_estimateCameraParameters(imagePoints, worldPoints, ...
    'EstimateSkew', false, 'EstimateTangentialDistortion', false, ...
    'NumRadialDistortionCoefficients', 2, 'WorldUnits', 'mm', ...
    'InitialIntrinsicMatrix', [], 'InitialRadialDistortion', []);

% 提取并保存相机参数到工作区

% 读取第一对图像以获取尺寸信息
I1 = imread(file1{1});
I2 = imread(file2{1});

% 相机内参
K1 = param.CameraParameters1.IntrinsicMatrix';
K2 = param.CameraParameters2.IntrinsicMatrix';

% 相机外参
R1 = param.CameraParameters1.RotationMatrices(:,:,1)';
T1 = param.CameraParameters1.TranslationVectors(1,:)';
R2 = param.CameraParameters2.RotationMatrices(:,:,1)';
T2 = param.CameraParameters2.TranslationVectors(1,:)';

% 计算投影矩阵
Lcam = K1 * [R1 T1];
Rcam = K2 * [R2 T2];

% 计算相机在世界坐标系中的位置
CL = -R1' * T1;
CR = -R2' * T2;

% View reprojection errors
h1=figure; showReprojectionErrors(param);

% Visualize pattern locations
h2=figure; showExtrinsics(param, 'CameraCentric');

% Display parameter estimation errors
displayErrors(estimationErrors, param);




% 显示关键参数
disp('Camera 1 内参矩阵 (K1):');
disp(K1);
disp('Camera 2 内参矩阵 (K2):');
disp(K2);
disp('相机间距离 (mm):');
disp(norm(CR-CL));
%{
% You can use the calibration data to undistort images
I1 = imread(file1{1});
I2 = imread(file2{1});

D1 = undistortImage(I1, param.CameraParameters1);
D2 = undistortImage(I2, param.CameraParameters2);

figure;subplot(1,2,1);imshow(I1);
subplot(1,2,2);imshow(I2);
figure;subplot(1,2,1);imshow(D1);
subplot(1,2,2);imshow(D2);

% You can use the calibration data to rectify stereo images.
[J1, J2] = my_rectifyStereoImages(I1, I2, param,'OutputView','full');
figure;imshowpair(J1,J2,'falsecolor','ColorChannels','red-cyan');


% select displayed checkeroard detection point grount truth 
% estimated point positions and camera positions.
cno=1;

Wpoints=[worldPoints zeros(size(worldPoints,1),1)];
figure;hold on;
axis vis3d; axis image;
grid on;
plot3(Wpoints(:,1),Wpoints(:,2),Wpoints(:,3),'b.','MarkerSize',20)

K1=param.CameraParameters1.IntrinsicMatrix';
R1=param.CameraParameters1.RotationMatrices(:,:,cno)';
T1=param.CameraParameters1.TranslationVectors(cno,:)';

Lcam=K1*[R1 T1];

K2=param.CameraParameters2.IntrinsicMatrix';
R2=param.CameraParameters2.RotationMatrices(:,:,cno)';
T2=param.CameraParameters2.TranslationVectors(cno,:)';


Rcam=K2*[R2 T2];

[points3d] = mytriangulate(imagePoints{1}(:,:,cno), imagePoints{2}(:,:,cno), Lcam,Rcam );
plot3(points3d(:,1),points3d(:,2),points3d(:,3),'r.')


% referencePoint(0,0,0)= R*Camera+T, So Camera=-inv(R)*T;
CL=-R1'*T1;
CR=-R2'*T2;

plot3(CR(1),CR(2),CR(3),'gs','MarkerFaceColor','g');
plot3(CL(1),CL(2),CL(3),'cs','MarkerFaceColor','c');
legend({'ground truth point locations','Calculated point locations','Camera2 position','Camera1 Position'});


% calculate relative distance from camera1 to camera2 in two different way
dist_1=norm(param.TranslationOfCamera2)
dist_2=norm(CR-CL)




% set the projection plane. I just project all pixel on to Z=0 plane
Z=0;

O=zeros(size(I1));
% remapping
for i=1:size(I1,1)
    i
    for j=1:size(I1,2)
        X=inv([Lcam(:,1:2) [-1*j;-1*i;-1]])*(-Z*Lcam(:,3)-Lcam(:,4));
        P=Rcam*[X(1);X(2);Z;1];
        P=fix(P/P(end));
        if P(1)>0 & P(2)<size(I2,1) & P(2)>0 & P(1)<size(I2,2)
            O(i,j,:)=I2(P(2),P(1),:);
        end
    end
end
figure;imshow(uint8(O))
figure;imshowpair(I1,uint8(O),'falsecolor','ColorChannels','red-cyan');
%}