// main.js - 上传和拍照功能（合并两个 DOMContentLoaded 监听器）
document.addEventListener('DOMContentLoaded', function() {
    // 获取功能卡片
    const uploadButtons = document.querySelectorAll('.service');
    let uploadDiv = null;
    let cameraDiv = document.getElementById('camera-div'); // 优先通过 id 获取

    uploadButtons.forEach(div => {
        const h3 = div.querySelector('h3');
        if (h3) {
            if (h3.textContent === 'Upload') {
                uploadDiv = div;
            } else if (h3.textContent === 'Take photos') {
                cameraDiv = div; // 如果找到了 Take photos 卡片，也更新 cameraDiv
            }
        }
    });

    // ---------- Upload 卡片跳转 ----------
    if (uploadDiv) {
        uploadDiv.addEventListener('click', function() {
            window.location.href = 'index-2.html'; // 跳转到检测页面
        });
    }

    // ---------- 拍照功能 ----------
    if (cameraDiv) {
        const cameraModal = document.getElementById('cameraModal');

        // 摄像头相关变量
        let stream = null;                      // 当前视频流
        let currentFacingMode = 'environment';  // 默认后置摄像头 (用于 facingMode 模式)
        let currentDeviceId = null;              // 当前使用的设备 ID (用于 deviceId 模式)
        let devices = [];                        // 所有视频输入设备列表

        // 点击卡片打开摄像头模态框
        cameraDiv.addEventListener('click', async function() {
            cameraModal.style.display = 'flex';
            await getCameraDevices(); // 先获取设备列表
            await startCamera();      // 启动摄像头（无参数，使用默认逻辑）
        });

        // 关闭按钮
        document.getElementById('closeCamera').addEventListener('click', function() {
            stopCamera();
            cameraModal.style.display = 'none';
        });

        // 切换摄像头按钮
        document.getElementById('switchCamera').addEventListener('click', async function() {
            await switchCamera();
        });

        // 拍照按钮
        document.getElementById('captureBtn').addEventListener('click', function() {
            capturePhoto();
        });

        // 获取所有可用的摄像头设备
        async function getCameraDevices() {
            try {
                const allDevices = await navigator.mediaDevices.enumerateDevices();
                devices = allDevices.filter(device => device.kind === 'videoinput');
                console.log('可用摄像头:', devices);
                return devices;
            } catch (error) {
                console.error('获取摄像头设备失败:', error);
                return [];
            }
        }

        // 启动摄像头 - 可接受可选参数 { deviceId, facingMode }
        async function startCamera(options = {}) {
            stopCamera(); // 先停止之前的流

            // 确保设备列表非空
            if (devices.length === 0) {
                await getCameraDevices();
            }

            try {
                // 构建视频约束
                let constraints = {
                    video: {
                        width: { ideal: 1280 },
                        height: { ideal: 720 }
                    },
                    audio: false
                };

                // 1. 如果传入了 deviceId，优先使用
                if (options.deviceId) {
                    constraints.video.deviceId = { exact: options.deviceId };
                    currentDeviceId = options.deviceId;
                    currentFacingMode = null; // 使用物理设备时清空 facingMode
                }
                // 2. 否则如果传入了 facingMode，使用 facingMode
                else if (options.facingMode) {
                    constraints.video.facingMode = { exact: options.facingMode };
                    currentFacingMode = options.facingMode;
                    currentDeviceId = null;
                }
                // 3. 没有传入参数，使用默认逻辑（基于设备和当前状态）
                else {
                    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
                    if (isMobile && devices.length > 0) {
                        // 移动设备单摄像头：使用 facingMode
                        constraints.video.facingMode = currentFacingMode;
                    } else if (devices.length > 1 && currentDeviceId) {
                        // 多摄像头且有已保存的 deviceId，使用它
                        constraints.video.deviceId = { exact: currentDeviceId };
                    } else if (devices.length > 1) {
                        // 多摄像头但没有 deviceId，默认使用第一个设备
                        constraints.video.deviceId = { exact: devices[0].deviceId };
                        currentDeviceId = devices[0].deviceId;
                    }
                    // 否则不指定具体约束，让浏览器自动选择
                }

                console.log('摄像头约束:', constraints);
                stream = await navigator.mediaDevices.getUserMedia(constraints);
                const video = document.getElementById('cameraPreview');
                video.srcObject = stream;

                // 等待视频加载并播放
                await new Promise((resolve, reject) => {
                    video.onloadedmetadata = async () => {
                        try {
                            await video.play();
                            resolve();
                        } catch (playError) {
                            reject(playError);
                        }
                    };
                });

                // 获取当前实际使用的设备信息（用于后续切换）
                const track = stream.getVideoTracks()[0];
                const settings = track.getSettings();
                if (settings.deviceId) {
                    currentDeviceId = settings.deviceId;
                }
                if (settings.facingMode) {
                    currentFacingMode = settings.facingMode;
                }

                // 更新设备列表（例如连接 iPhone 摄像头后可能新增设备）
                await getCameraDevices();

            } catch (error) {
                console.error('启动摄像头失败:', error);

                // 尝试降级：只请求 video: true
                try {
                    const fallbackStream = await navigator.mediaDevices.getUserMedia({ video: true });
                    const video = document.getElementById('cameraPreview');
                    video.srcObject = fallbackStream;
                    await video.play();
                    stream = fallbackStream;

                    // 降级后尝试获取 settings
                    const track = stream.getVideoTracks()[0];
                    const settings = track.getSettings();
                    if (settings.deviceId) currentDeviceId = settings.deviceId;
                    if (settings.facingMode) currentFacingMode = settings.facingMode;

                } catch (fallbackError) {
                    console.error('降级启动也失败:', fallbackError);
                    handleCameraError(fallbackError);
                }
            }
        }

        // 摄像头错误处理
        function handleCameraError(error) {
            let message = '无法访问摄像头：';
            if (error.name === 'NotFoundError' || error.name === 'DevicesNotFoundError') {
                message += '未找到摄像头设备。';
            } else if (error.name === 'NotAllowedError' || error.name === 'PermissionDeniedError') {
                message += '摄像头权限被拒绝。请检查浏览器设置。';
            } else if (error.name === 'NotReadableError' || error.name === 'TrackStartError') {
                message += '摄像头可能被其他应用占用。';
            } else {
                message += error.message;
            }
            alert(message);
        }

        // 切换摄像头
        async function switchCamera() {
            if (!stream) return;

            const track = stream.getVideoTracks()[0];
            const settings = track.getSettings();

            // 检查当前设备是否支持 facingMode 切换
            const capabilities = track.getCapabilities ? track.getCapabilities() : {};
            const canSwitchFacingMode = capabilities.facingMode && capabilities.facingMode.length > 1;

            if (canSwitchFacingMode) {
                // 在同一设备内切换 facingMode
                const newFacingMode = currentFacingMode === 'environment' ? 'user' : 'environment';
                try {
                    // 注意：使用相同的 deviceId 但新的 facingMode 重新启动摄像头
                    await startCamera({ deviceId: currentDeviceId, facingMode: newFacingMode });
                    return;
                } catch (err) {
                    console.warn('切换 facingMode 失败，尝试切换到其他物理设备', err);
                }
            }

            // 无法在同一设备内切换 facingMode，则切换到下一个物理设备
            // 先确保设备列表最新
            await getCameraDevices();
            const videoDevices = devices.filter(d => d.kind === 'videoinput');

            if (videoDevices.length <= 1) {
                alert('当前只有一个摄像头，无法切换');
                return;
            }

            // 找到当前设备在列表中的索引
            const currentIdx = videoDevices.findIndex(d => d.deviceId === currentDeviceId);
            // 计算下一个索引（如果找不到当前设备，则从0开始）
            const nextIdx = currentIdx === -1 ? 0 : (currentIdx + 1) % videoDevices.length;
            const nextDevice = videoDevices[nextIdx];

            // 切换到下一个设备
            await startCamera({ deviceId: nextDevice.deviceId });
        }

        // 停止摄像头
        function stopCamera() {
            if (stream) {
                stream.getTracks().forEach(track => track.stop());
                stream = null;
            }
            const video = document.getElementById('cameraPreview');
            if (video.srcObject) {
                video.srcObject = null;
            }
        }

        // 页面卸载时停止摄像头
        window.addEventListener('beforeunload', function() {
            stopCamera();
        });

        // 点击模态框背景关闭
        cameraModal.addEventListener('click', function(e) {
            if (e.target === cameraModal) {
                stopCamera();
                cameraModal.style.display = 'none';
            }
        });

        // 拍照函数
        function capturePhoto() {
            const video = document.getElementById('cameraPreview');
            const canvas = document.getElementById('photoCanvas');
            const context = canvas.getContext('2d');

            // 确保视频已加载
            if (video.videoWidth === 0 || video.videoHeight === 0) {
                alert('摄像头未就绪，请稍后重试。');
                return;
            }

            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            context.drawImage(video, 0, 0, canvas.width, canvas.height);

            canvas.toBlob(async function(blob) {
                const timestamp = new Date().getTime();
                const fileName = `photo_${timestamp}.jpg`;

                const file = new File([blob], fileName, {
                    type: 'image/jpeg',
                    lastModified: timestamp
                });

                // 获取 GPS 坐标
                let gpsInfo = {};
                if (navigator.geolocation) {
                    try {
                        const position = await new Promise((resolve, reject) => {
                            navigator.geolocation.getCurrentPosition(resolve, reject, {
                                enableHighAccuracy: true,
                                timeout: 10000,
                                maximumAge: 0
                            });
                        });
                        gpsInfo = {
                            latitude: position.coords.latitude,
                            longitude: position.coords.longitude,
                            accuracy: position.coords.accuracy
                        };
                        console.log('GPS信息:', gpsInfo);
                    } catch (error) {
                        console.warn('GPS获取失败:', error);
                        // GPS失败不影响拍照，继续处理照片
                    }
                }

                // 处理照片文件（上传 + 检测）
                await handleFileUpload([file], gpsInfo);

                // 停止摄像头并关闭模态框
                stopCamera();
                cameraModal.style.display = 'none';

                // 显示拍照成功消息
                const message = gpsInfo.latitude ?
                    `照片已捕获！位置：${gpsInfo.latitude.toFixed(6)}, ${gpsInfo.longitude.toFixed(6)}` :
                    '照片已捕获！';
                alert(message);

            }, 'image/jpeg', 0.9);
        }
    }

    // ---------- 统一处理文件上传 + 检测 ----------
    async function handleFileUpload(files, gpsInfo = {}) {
        console.log('🚀 handleFileUpload 被调用，文件数量:', files.length);

        // 只处理第一张图片
        const file = files[0];
        if (!file) return;

        console.log('📁 准备上传:', file.name, file.type, (file.size / 1024).toFixed(2) + 'KB');

        const formData = new FormData();
        formData.append('file', file);

        try {
            console.log('📡 发送请求至 http://127.0.0.1:5001/detect');
            const response = await fetch('http://localhost:5001/detect', {
                method: 'POST',
                body: formData,
                mode: 'cors',
                credentials: 'omit'
            });

            console.log('📨 响应状态:', response.status);
            if (!response.ok) {
                const error = await response.json();
                alert('检测失败：' + error.error);
                return;
            }

            const blob = await response.blob();
            const imageUrl = URL.createObjectURL(blob);

            // 显示检测结果图片
            const resultImg = document.getElementById('result-img');
            if (resultImg) {
                resultImg.src = imageUrl;
                // 如果 result-img 有父容器，可以在后面添加地图链接
                addMapLinkIfNeeded(gpsInfo, resultImg.parentNode);
            } else {
                // 如果没有 result-img 元素，则创建一个
                const newImg = document.createElement('img');
                newImg.src = imageUrl;
                newImg.style.maxWidth = '100%';
                newImg.style.marginTop = '20px';
                document.body.appendChild(newImg);
                addMapLinkIfNeeded(gpsInfo, document.body);
            }

            alert('✅ 检测完成！');

        } catch (err) {
            console.error('❌ fetch 失败:', err);
            alert('网络错误，无法连接到检测服务，请确保后端已启动（http://127.0.0.1:5001）');
        }
    }

    // 辅助函数：如果存在 GPS 信息，在指定容器中添加谷歌地图链接
    function addMapLinkIfNeeded(gpsInfo, container) {
        if (gpsInfo.latitude && gpsInfo.longitude) {
            // 移除可能已存在的地图链接
            const existingLink = document.getElementById('map-link');
            if (existingLink) existingLink.remove();

            const mapLink = document.createElement('a');
            mapLink.id = 'map-link';
            mapLink.href = `https://www.google.com/maps?q=${gpsInfo.latitude},${gpsInfo.longitude}`;
            mapLink.target = '_blank';
            mapLink.textContent = '📍 在谷歌地图上查看位置';
            mapLink.style.display = 'block';
            mapLink.style.marginTop = '10px';
            mapLink.style.padding = '8px';
            mapLink.style.backgroundColor = '#f0f0f0';
            mapLink.style.borderRadius = '4px';
            mapLink.style.textAlign = 'center';
            mapLink.style.textDecoration = 'none';
            mapLink.style.color = '#4285f4';
            container.appendChild(mapLink);
        }
    }
});