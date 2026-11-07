// FixPack Frontend Application Logic

// Tab Switching
function switchTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));

    const targetTab = document.getElementById(`tab-${tabId}`);
    const targetBtn = document.getElementById(`tab-btn-${tabId}`);
    if (targetTab) targetTab.classList.remove('hidden');
    if (targetBtn) targetBtn.classList.add('active');

    if (tabId === 'calendar') loadPosts();
    if (tabId === 'users') loadUsers();
}

// Live Character Counter & Facebook Preview
document.addEventListener('DOMContentLoaded', () => {
    const captionEl = document.getElementById('post-caption');
    const previewTextEl = document.getElementById('preview-text');
    const counterEl = document.getElementById('caption-counter');
    const topicEl = document.getElementById('post-topic');

    // Default Date to Tomorrow
    const dateInput = document.getElementById('post-date');
    if (dateInput) {
        const tomorrow = new Date();
        tomorrow.setDate(tomorrow.getDate() + 1);
        dateInput.value = tomorrow.toISOString().split('T')[0];
    }

    if (captionEl) {
        captionEl.addEventListener('input', (e) => {
            const val = e.target.value;
            counterEl.textContent = `${val.length} ตัวอักษร`;
            previewTextEl.textContent = val || "เขียนแคปชั่นของคุณที่นี่ หรือคลิกปุ่ม 'ให้ AI แต่งแคปชั่น' ด้านบน...";
        });
    }

    // Color Pickers sync
    const primaryPicker = document.getElementById('ci-primary');
    const primaryText = document.getElementById('ci-primary-text');
    if (primaryPicker && primaryText) {
        primaryPicker.addEventListener('input', (e) => primaryText.value = e.target.value);
        primaryText.addEventListener('input', (e) => primaryPicker.value = e.target.value);
    }

    const accentPicker = document.getElementById('ci-accent');
    const accentText = document.getElementById('ci-accent-text');
    if (accentPicker && accentText) {
        accentPicker.addEventListener('input', (e) => accentText.value = e.target.value);
        accentText.addEventListener('input', (e) => accentPicker.value = e.target.value);
    }

    loadPosts();
});

// Global state for images
let currentUploadedImagePath = "";

// Update Image choice for Preview
function updateImageChoice(choice) {
    const previewImg = document.getElementById('preview-img');
    const previewContainer = document.getElementById('preview-image-container');
    const pathInput = document.getElementById('selected-image-path');
    const subBanner = document.getElementById('subpanel-banner');
    const subUpload = document.getElementById('subpanel-upload');

    // Reset styles
    ['banner', 'upload', 'technician', 'none'].forEach(id => {
        const lbl = document.getElementById(`label-img-${id}`);
        if (lbl) {
            lbl.classList.remove('border-[#FF5B00]', 'bg-orange-50/40');
            lbl.classList.add('border-slate-200');
        }
    });

    const activeLbl = document.getElementById(`label-img-${choice}`);
    if (activeLbl) {
        activeLbl.classList.remove('border-slate-200');
        activeLbl.classList.add('border-[#FF5B00]', 'bg-orange-50/40');
    }

    // Toggle sub-action panels
    if (subBanner) subBanner.classList.add('hidden');
    if (subUpload) subUpload.classList.add('hidden');

    if (choice === 'banner') {
        if (subBanner) subBanner.classList.remove('hidden');
        previewContainer.classList.remove('hidden');
        const bannerSrc = document.getElementById('img-thumb-banner') ? document.getElementById('img-thumb-banner').src : '/static/fixpack_ai_banner.png';
        previewImg.src = bannerSrc;
        if (pathInput) pathInput.value = "fixpack_ai_banner.png";
    } else if (choice === 'upload') {
        if (subUpload) subUpload.classList.remove('hidden');
        previewContainer.classList.remove('hidden');
        if (currentUploadedImagePath) {
            previewImg.src = currentUploadedImagePath.startsWith('/') ? currentUploadedImagePath : '/' + currentUploadedImagePath;
            if (pathInput) pathInput.value = currentUploadedImagePath;
            const visionRow = document.getElementById('upload-vision-ai-row');
            if (visionRow) visionRow.classList.remove('hidden');
        } else {
            previewImg.src = '/static/cover.jpg';
        }
    } else if (choice === 'technician') {
        previewContainer.classList.remove('hidden');
        previewImg.src = '/static/ai_technician.jpg';
        if (pathInput) pathInput.value = "ai_technician.jpg";
    } else {
        previewContainer.classList.add('hidden');
        if (pathInput) pathInput.value = "";
    }
}

// Upload custom image
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;

    const filenameText = document.getElementById('upload-filename-text');
    const previewBox = document.getElementById('upload-preview-box');
    const enhanceRow = document.getElementById('upload-enhance-row');
    const pathInput = document.getElementById('selected-image-path');
    const previewImg = document.getElementById('preview-img');

    if (filenameText) filenameText.textContent = `กำลังอัปโหลด: ${file.name}...`;

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/api/upload_image', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            currentUploadedImagePath = data.image_path;
            if (pathInput) pathInput.value = data.image_path;
            if (previewImg) previewImg.src = data.url;
            if (filenameText) filenameText.textContent = `✓ ${file.name}`;
            if (previewBox) {
                previewBox.innerHTML = `<img src="${data.url}" class="w-full h-full object-cover">`;
            }
            if (enhanceRow) enhanceRow.classList.remove('hidden');
            const visionRow = document.getElementById('upload-vision-ai-row');
            if (visionRow) visionRow.classList.remove('hidden');

            Swal.fire({
                icon: 'success',
                title: 'อัปโหลดรูปภาพสำเร็จ!',
                html: `
                    <p class="text-xs text-slate-600 mb-3">รูปภาพหน้างานจริงพร้อมใช้งานแล้ว</p>
                    <div class="text-left text-xs bg-purple-50 p-3 rounded-xl border border-purple-200 text-purple-900 space-y-1">
                        <p class="font-bold">✨ ตัวช่วยพิเศษสำหรับโพสต์นี้:</p>
                        <p>1. กดปุ่ม <strong>"ให้ AI แต่งแคปชั่นจากรูปนี้"</strong> เพื่อให้ AI วิเคราะห์รูปและคิดข้อความให้เลย</p>
                        <p>2. หรือกดปุ่ม <strong>"ให้ AI ใส่กรอบแบรนด์"</strong> เพื่อประทับตราโลโก้และเบอร์ติดต่อลงบนภาพ</p>
                    </div>
                `,
                confirmButtonText: 'ตกลง',
                confirmButtonColor: '#0B3B60'
            });
        } else {
            Swal.fire('อัปโหลดล้มเหลว', data.error || 'ไม่สามารถอัปโหลดไฟล์ได้', 'error');
        }
    } catch (e) {
        Swal.fire('เกิดข้อผิดพลาด', 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์เพื่ออัปโหลดไฟล์ได้', 'error');
    }
}

// Vision AI: Analyze uploaded photo and generate marketing post
async function generateCaptionFromUploadedImage() {
    if (!currentUploadedImagePath) {
        Swal.fire('แจ้งเตือน', 'กรุณาอัปโหลดรูปภาพก่อนให้ AI วิเคราะห์', 'warning');
        return;
    }

    const hint = document.getElementById('post-topic') ? document.getElementById('post-topic').value : '';
    const activeName = document.getElementById('current-page-label') ? document.getElementById('current-page-label').textContent : 'เพจ';

    Swal.fire({
        title: '🤖 AI กำลังดูรูปภาพ & คิดแคปชั่น...',
        text: `ระบบกำลังวิเคราะห์ภาพจริง และแต่งหัวข้อกับแคปชั่นการตลาดให้ตรงกับเพจ "${activeName}"...`,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/ai/caption_from_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_path: currentUploadedImagePath,
                user_hint: hint
            })
        });
        const data = await res.json();
        Swal.close();

        if (data.success) {
            const topicInput = document.getElementById('post-topic');
            const captionInput = document.getElementById('post-caption');
            const previewText = document.getElementById('preview-text');
            const counter = document.getElementById('caption-counter');

            if (topicInput && data.topic) {
                topicInput.value = data.topic;
            }
            if (captionInput && data.caption) {
                captionInput.value = data.caption;
                if (counter) counter.textContent = `${data.caption.length} ตัวอักษร`;
                if (previewText) previewText.textContent = data.caption;
            }

            Swal.fire({
                icon: 'success',
                title: '✨ AI แต่งแคปชั่นจากรูปภาพเรียบร้อย!',
                html: `
                    <p class="text-sm text-slate-600 mb-2">หัวข้อ: <strong>${data.topic || ''}</strong></p>
                    <div class="p-3 bg-blue-50 text-blue-900 rounded-xl text-xs font-semibold text-left border border-blue-200">
                        💡 <strong>เนื้อหาถูกใส่ลงในช่องแคปชั่นแล้ว:</strong> คุณสามารถตรวจทาน ปรับแต่ง หรือพิมพ์แก้ไขเนื้อหาได้ตามใจชอบก่อนกดโพสต์
                    </div>
                `,
                confirmButtonText: 'ไปตรวจทาน / แก้ไขเนื้อหา',
                confirmButtonColor: '#0B3B60'
            });
        } else {
            Swal.fire('เกิดข้อผิดพลาด', data.error || 'AI ไม่สามารถวิเคราะห์รูปภาพได้', 'error');
        }
    } catch (e) {
        Swal.fire('เกิดข้อผิดพลาด', 'ไม่สามารถเชื่อมต่อระบบ AI ได้: ' + e.message, 'error');
    }
}

// Enhance uploaded image with brand CI overlay
async function enhanceUploadedImageWithCI() {
    if (!currentUploadedImagePath) {
        Swal.fire('แจ้งเตือน', 'กรุณาอัปโหลดรูปภาพก่อนทำการตกแต่ง', 'warning');
        return;
    }

    const topic = document.getElementById('post-topic').value || 'ผลงานซ่อมจริงจากช่าง FixPack';
    const previewImg = document.getElementById('preview-img');
    const pathInput = document.getElementById('selected-image-path');
    const previewBox = document.getElementById('upload-preview-box');

    Swal.fire({
        title: 'AI กำลังตกแต่งรูปภาพ...',
        text: 'กำลังใส่กรอบ CI แบรนด์ FixPack, ป้ายราคาเหมา 1,500.- และข้อมูลติดต่อ',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/ai/enhance_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image_path: currentUploadedImagePath,
                title: topic,
                subtitle: 'งานเรียบร้อย ปลอดภัย จบไวในแพ็กเกจเดียว'
            })
        });
        const data = await res.json();
        Swal.close();

        if (data.success) {
            currentUploadedImagePath = data.image_path;
            if (pathInput) pathInput.value = data.image_path;
            if (previewImg) previewImg.src = data.url + '?t=' + Date.now();
            if (previewBox) {
                previewBox.innerHTML = `<img src="${data.url}?t=${Date.now()}" class="w-full h-full object-cover">`;
            }
            Swal.fire({
                icon: 'success',
                title: 'ตกแต่งภาพตาม CI แบรนด์สำเร็จ!',
                text: 'รูปภาพถูกใส่กรอบแบรนด์และป้ายราคาเรียบร้อยแล้ว ดูตัวอย่างบนจอมือถือได้ทันที',
                confirmButtonColor: '#0B3B60'
            });
        } else {
            Swal.fire('ผิดพลาด', data.error || 'ไม่สามารถตกแต่งภาพได้', 'error');
        }
    } catch (e) {
        Swal.fire('ผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

// Generate new banner using AI based on topic
async function generateNewBannerWithAI() {
    const topic = document.getElementById('post-topic').value || 'บริการช่างซ่อมแซมบ้าน FixPack';
    const previewImg = document.getElementById('preview-img');
    const pathInput = document.getElementById('selected-image-path');
    const thumbBanner = document.getElementById('img-thumb-banner');

    Swal.fire({
        title: 'AI กำลังสร้างแบนเนอร์ใหม่...',
        text: `กำลังออกแบบแบนเนอร์สำหรับหัวข้อ: ${topic}`,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/ai/generate_banner', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });
        const data = await res.json();
        Swal.close();

        if (data.success) {
            if (pathInput) pathInput.value = data.image_path;
            const freshUrl = data.url + '?t=' + Date.now();
            if (previewImg) previewImg.src = freshUrl;
            if (thumbBanner) thumbBanner.src = freshUrl;

            Swal.fire({
                icon: 'success',
                title: 'สร้างแบนเนอร์สำเร็จ!',
                confirmButtonColor: '#0B3B60'
            });
        } else {
            Swal.fire('ผิดพลาด', data.error || 'ไม่สามารถสร้างแบนเนอร์ได้', 'error');
        }
    } catch (e) {
        Swal.fire('ผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

// Random Topic and generate caption in one click
async function randomTopicAndCaption() {
    try {
        const res = await fetch('/api/ai/random_topic');
        const data = await res.json();
        if (data.success && data.topic) {
            document.getElementById('post-topic').value = data.topic;
            // Now generate caption
            generateCaptionWithAI();
        }
    } catch (e) {
        console.error(e);
    }
}

// Load Scheduled Posts
async function loadPosts() {
    const container = document.getElementById('posts-container');
    if (!container) return;

    try {
        const res = await fetch('/api/posts');
        const posts = await res.json();

        // Update stats
        let total = posts.length;
        let pending = posts.filter(p => p.status === 'pending').length;
        let posted = posts.filter(p => p.status === 'posted').length;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-pending').textContent = pending;
        document.getElementById('stat-posted').textContent = posted;
        document.getElementById('post-count-badge').textContent = `${total} รายการ`;

        if (posts.length === 0) {
            container.innerHTML = `
                <div class="text-center py-12 bg-white rounded-2xl border border-slate-200">
                    <div class="w-16 h-16 rounded-full bg-orange-100 text-[#FF5B00] flex items-center justify-center mx-auto mb-3 text-2xl">
                        <i class="fa-solid fa-calendar-xmark"></i>
                    </div>
                    <h3 class="font-bold text-slate-700 text-lg">ยังไม่มีรายการโพสต์ที่ตั้งเวลาไว้</h3>
                    <p class="text-sm text-slate-500 mt-1 max-w-md mx-auto">
                        ไม่ต้องกังวล! เมื่อถึงเวลาประจำวัน ระบบ Auto-Pilot จะใช้ AI สุ่มคิดหัวข้องานช่างและโพสต์ให้เองอัตโนมัติ
                    </p>
                    <button onclick="switchTab('create')" class="mt-4 px-4 py-2 bg-[#0B3B60] text-white text-sm font-medium rounded-xl hover:bg-[#082b47] transition">
                        + เพิ่มโพสต์ล่วงหน้าเลย
                    </button>
                </div>
            `;
            return;
        }

        container.innerHTML = posts.map(post => {
            const isPending = post.status === 'pending';
            const isPosted = post.status === 'posted';
            const statusBadge = isPending 
                ? '<span class="px-2.5 py-1 rounded-full bg-amber-100 text-amber-700 font-semibold text-xs flex items-center gap-1"><i class="fa-solid fa-clock"></i> รอคิวโพสต์</span>'
                : (isPosted 
                    ? '<span class="px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-700 font-semibold text-xs flex items-center gap-1"><i class="fa-solid fa-circle-check"></i> โพสต์แล้ว</span>'
                    : '<span class="px-2.5 py-1 rounded-full bg-red-100 text-red-700 font-semibold text-xs flex items-center gap-1"><i class="fa-solid fa-triangle-exclamation"></i> ผิดพลาด</span>');

            let imgSrc = '';
            if (post.image_path) {
                if (post.image_path.startsWith('/')) {
                    imgSrc = post.image_path;
                } else if (post.image_path.startsWith('static/')) {
                    imgSrc = '/' + post.image_path;
                } else {
                    imgSrc = '/static/' + post.image_path;
                }
            }
            const imgTag = imgSrc 
                ? `<img src="${imgSrc}" class="w-16 h-16 rounded-xl object-cover border border-slate-200 shrink-0" onerror="this.src='/static/profile.jpg'">`
                : `<div class="w-16 h-16 rounded-xl bg-slate-100 text-slate-400 flex items-center justify-center shrink-0 text-xl"><i class="fa-solid fa-align-left"></i></div>`;

            return `
                <div class="bg-white p-5 rounded-2xl shadow-sm border border-slate-200 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 transition hover:shadow-md">
                    <div class="flex items-start gap-4 flex-1">
                        ${imgTag}
                        <div class="space-y-1">
                            <div class="flex items-center gap-2.5 flex-wrap">
                                <span class="text-sm font-bold text-[#0B3B60] bg-blue-50 px-2.5 py-0.5 rounded-lg border border-blue-100">
                                    📅 ${post.date} เวลา ${post.time} น.
                                </span>
                                ${statusBadge}
                                ${post.type === 'autopilot_generated' ? '<span class="text-[11px] px-2 py-0.5 rounded bg-purple-100 text-purple-700 font-medium">🤖 Auto-Pilot</span>' : ''}
                            </div>
                            <h4 class="font-bold text-slate-800 text-sm">
                                ${post.topic || 'โพสต์ FixPack (ไม่มีระบุหัวข้อ)'}
                            </h4>
                            <p class="text-xs text-slate-500 line-clamp-2 leading-relaxed">
                                ${post.content || '💡 ให้ AI เขียนเนื้อหาให้อัตโนมัติเมื่อถึงเวลาโพสต์'}
                            </p>
                        </div>
                    </div>

                    <!-- Actions -->
                    <div class="flex items-center gap-2 self-end md:self-center shrink-0">
                        ${isPending ? `
                            <button onclick="postSingleNow('${post.id}')" class="px-3.5 py-1.5 bg-[#FF5B00] hover:bg-[#e05000] text-white text-xs font-semibold rounded-lg shadow-xs transition flex items-center gap-1">
                                <i class="fa-solid fa-paper-plane"></i> โพสต์ทันที
                            </button>
                        ` : ''}
                        ${post.post_url ? `
                            <a href="${post.post_url}" target="_blank" class="px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-700 text-xs font-semibold rounded-lg transition flex items-center gap-1">
                                <i class="fa-brands fa-facebook"></i> ดูบน Facebook
                            </a>
                        ` : ''}
                        <button onclick="deletePost('${post.id}')" class="p-2 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition" title="ลบรายการ">
                            <i class="fa-solid fa-trash-can"></i>
                        </button>
                    </div>
                </div>
            `;
        }).join('');

    } catch (err) {
        container.innerHTML = `<div class="p-4 text-center text-red-500">เกิดข้อผิดพลาดในการโหลดโพสต์: ${err}</div>`;
    }
}

// Generate Caption with AI
async function generateCaptionWithAI() {
    const topicInput = document.getElementById('post-topic');
    const captionEl = document.getElementById('post-caption');
    const topic = topicInput.value.trim() || "บริการช่างซ่อมแซมบ้านครบวงจร";

    Swal.fire({
        title: 'กำลังให้ AI คิดแคปชั่น...',
        html: `สำหรับหัวข้อ: <strong>"${topic}"</strong>`,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/ai/generate_caption', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic: topic })
        });
        const data = await res.json();
        Swal.close();

        if (data.success && data.caption) {
            captionEl.value = data.caption;
            captionEl.dispatchEvent(new Event('input'));
            Swal.fire({
                icon: 'success',
                title: 'เขียนแคปชั่นสำเร็จ!',
                timer: 1500,
                showConfirmButton: false
            });
        } else {
            Swal.fire('ข้อผิดพลาด', data.error || 'ไม่สามารถสร้างแคปชั่นได้', 'error');
        }
    } catch (err) {
        Swal.fire('ข้อผิดพลาด', 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
    }
}

// Submit Post (Schedule or Post Now)
async function submitPost(mode) {
    const date = document.getElementById('post-date').value;
    const time = document.getElementById('post-time').value;
    const topic = document.getElementById('post-topic').value;
    const content = document.getElementById('post-caption').value;
    
    // Selected image
    const selectedImg = document.querySelector('input[name="image-choice"]:checked').value;
    let image_path = null;
    if (selectedImg === 'banner') {
        image_path = document.getElementById('selected-image-path').value || "fixpack_ai_banner.png";
    } else if (selectedImg === 'upload') {
        image_path = currentUploadedImagePath || "cover.jpg";
    } else if (selectedImg === 'technician') {
        image_path = "ai_technician.jpg";
    }

    if (mode === 'now') {
        const activeName = document.getElementById('current-page-label') ? document.getElementById('current-page-label').textContent : 'เพจ';
        const confirm = await Swal.fire({
            title: `ยืนยันการโพสต์ขึ้นเพจ "${activeName}"?`,
            text: 'ข้อความและรูปภาพจะถูกส่งไปยังเพจจริงทันที',
            icon: 'question',
            showCancelButton: true,
            confirmButtonColor: '#FF5B00',
            cancelButtonColor: '#64748b',
            confirmButtonText: '🚀 โพสต์ทันที',
            cancelButtonText: 'ยกเลิก'
        });
        if (!confirm.isConfirmed) return;
    }

    Swal.fire({
        title: mode === 'now' ? 'กำลังส่งข้อมูลไปยัง Facebook...' : 'กำลังบันทึกลงตาราง...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: date,
                time: time,
                topic: topic,
                content: content,
                image_path: image_path,
                post_immediately: (mode === 'now')
            })
        });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: mode === 'now' ? 'โพสต์ขึ้นเพจเรียบร้อยแล้ว!' : 'บันทึกลงตารางสำเร็จ!',
                text: result.url ? `ดูโพสต์ได้ที่: ${result.url}` : undefined,
                confirmButtonColor: '#0B3B60'
            });
            switchTab('calendar');
        } else {
            Swal.fire('เกิดข้อผิดพลาด', result.error, 'error');
        }
    } catch (err) {
        Swal.fire('ข้อผิดพลาด', 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
    }
}

// Delete Post
async function deletePost(postId) {
    const confirm = await Swal.fire({
        title: 'ต้องการลบโพสต์นี้?',
        text: 'รายการที่ลบจะไม่สามารถกู้คืนได้',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'ลบโพสต์',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/posts/${postId}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.success) {
            loadPosts();
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'ลบโพสต์ไม่สำเร็จ', 'error');
    }
}

// Post Single Now from Calendar
async function postSingleNow(postId) {
    Swal.fire({
        title: 'กำลังส่งข้อมูลไปยัง Facebook...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch(`/api/posts/${postId}/post_now`, { method: 'POST' });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'โพสต์สำเร็จแล้ว!',
                text: `ดูโพสต์ได้ที่ Facebook`,
                confirmButtonColor: '#0B3B60'
            });
            loadPosts();
        } else {
            Swal.fire('ผิดพลาด', result.error, 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อล้มเหลว', 'error');
    }
}

// AI Topic Planner Generator
async function generatePlan(days) {
    const container = document.getElementById('planner-results');
    container.innerHTML = `
        <div class="col-span-full text-center py-12">
            <i class="fa-solid fa-spinner fa-spin text-3xl text-[#FF5B00] mb-3"></i>
            <p class="text-slate-600 font-medium">AI กำลังวิเคราะห์และวางแผนคอนเทนต์ ${days} วันสำหรับ FixPack...</p>
        </div>
    `;

    try {
        const res = await fetch('/api/ai/plan_topics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days: days })
        });
        const data = await res.json();

        if (data.success && data.topics) {
            container.innerHTML = data.topics.map((t, idx) => `
                <div class="bg-white p-5 rounded-2xl border border-slate-200 shadow-sm flex flex-col justify-between hover:shadow-md transition">
                    <div>
                        <div class="flex justify-between items-center mb-2">
                            <span class="text-xs font-bold px-2 py-0.5 rounded bg-orange-100 text-[#FF5B00]">วันที่ ${idx + 1}</span>
                            <span class="text-xs text-slate-400">${t.category || 'งานช่าง'}</span>
                        </div>
                        <h4 class="font-bold text-slate-800 text-sm mb-2">${t.topic}</h4>
                        <p class="text-xs text-slate-500 leading-relaxed">${t.brief || ''}</p>
                    </div>
                    <button onclick="scheduleTopicDirectly('${encodeURIComponent(t.topic)}', ${idx + 1})" 
                            class="mt-4 w-full py-2 px-3 bg-slate-50 hover:bg-[#0B3B60] hover:text-white text-[#0B3B60] text-xs font-semibold rounded-xl border border-slate-200 transition flex items-center justify-center gap-1.5">
                        <i class="fa-solid fa-calendar-plus"></i> บรรจุลงตารางวันที่ ${idx + 1}
                    </button>
                </div>
            `).join('');
        }
    } catch (e) {
        container.innerHTML = `<div class="col-span-full p-4 text-center text-red-500">เกิดข้อผิดพลาดในการวางแผน</div>`;
    }
}

// Schedule topic directly from planner
async function scheduleTopicDirectly(encodedTopic, dayOffset) {
    const topic = decodeURIComponent(encodedTopic);
    const targetDate = new Date();
    targetDate.setDate(targetDate.getDate() + dayOffset);
    const dateStr = targetDate.toISOString().split('T')[0];

    try {
        const res = await fetch('/api/posts', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                date: dateStr,
                time: "09:30",
                topic: topic,
                content: "",
                image_path: "fixpack_ai_banner.png"
            })
        });
        const result = await res.json();
        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'บรรจุลงตารางแล้ว!',
                text: `กำหนดโพสต์วันที่ ${dateStr} เวลา 09:30 น.`,
                timer: 1500,
                showConfirmButton: false
            });
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'ไม่สามารถบันทึกได้', 'error');
    }
}

// Trigger Auto-Pilot Now
async function triggerAutoPilotNow() {
    const confirm = await Swal.fire({
        title: 'รัน Auto-Pilot ทันที?',
        text: 'ระบบจะให้ AI คิดหัวข้อใหม่ เขียนแคปชั่น และโพสต์ขึ้นเพจ FixPack เดี๋ยวนี้เลย 1 โพสต์',
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#0B3B60',
        cancelButtonColor: '#64748b',
        confirmButtonText: '🚀 รันทันที',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    Swal.fire({
        title: 'กำลังคิดหัวข้อและโพสต์ด้วย AI...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/autopilot/run_now', { method: 'POST' });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire('สำเร็จ!', 'AI โพสต์ขึ้นเพจ FixPack เรียบร้อยแล้ว', 'success');
            loadPosts();
        } else {
            Swal.fire('เกิดข้อผิดพลาด', result.error, 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อล้มเหลว', 'error');
    }
}

// Save Brand Config (Admin)
async function saveBrandConfig(e) {
    e.preventDefault();
    const data = {
        brand_name: document.getElementById('ci-name').value,
        tagline: document.getElementById('ci-tagline').value,
        primary_color: document.getElementById('ci-primary').value,
        accent_color: document.getElementById('ci-accent').value,
        phone: document.getElementById('ci-phone').value,
        price_tag: document.getElementById('ci-price').value,
        daily_post_time: document.getElementById('ci-daily-time').value
    };

    try {
        const res = await fetch('/api/admin/brand', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        if (result.success) {
            Swal.fire('สำเร็จ', 'บันทึกการตั้งค่า CI แบรนด์เรียบร้อยแล้ว', 'success');
        }
    } catch (err) {
        Swal.fire('ข้อผิดพลาด', 'บันทึกไม่สำเร็จ', 'error');
    }
}

// Load Users (Admin)
async function loadUsers() {
    const tbody = document.getElementById('user-table-body');
    if (!tbody) return;

    try {
        const res = await fetch('/api/admin/users');
        const users = await res.json();

        tbody.innerHTML = users.map(u => {
            const roleBadge = u.role === 'admin' 
                ? '<span class="px-2.5 py-1 rounded-full bg-purple-100 text-purple-700 font-semibold text-xs">Admin (สูงสุด)</span>'
                : (u.role === 'owner' 
                    ? '<span class="px-2.5 py-1 rounded-full bg-blue-100 text-blue-700 font-semibold text-xs">Page Owner (เจ้าของเพจ)</span>'
                    : '<span class="px-2.5 py-1 rounded-full bg-slate-100 text-slate-700 font-semibold text-xs">Staff (ทีมงาน)</span>');

            return `
                <tr class="hover:bg-slate-50 transition">
                    <td class="py-3 px-4 font-bold text-slate-800">${u.username}</td>
                    <td class="py-3 px-4 text-slate-600">${u.name}</td>
                    <td class="py-3 px-4">${roleBadge}</td>
                    <td class="py-3 px-4 text-right">
                        ${u.username !== 'admin' ? `
                            <button onclick="deleteUser('${u.username}')" class="text-red-500 hover:text-red-700 text-xs font-semibold">
                                <i class="fa-solid fa-trash-can"></i> ลบ
                            </button>
                        ` : '<span class="text-slate-400 text-xs">สงวนสิทธิ์</span>'}
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="4" class="p-4 text-center text-red-500">โหลดผู้ใช้ไม่สำเร็จ</td></tr>';
    }
}

// Add User Modal
async function openAddUserModal() {
    const { value: formValues } = await Swal.fire({
        title: 'เพิ่มผู้ใช้งานใหม่',
        html: `
            <div class="space-y-3 text-left">
                <div>
                    <label class="text-xs font-semibold text-slate-600">ชื่อผู้ใช้งาน (Username)</label>
                    <input id="swal-username" class="w-full px-3 py-2 border rounded-xl text-sm" placeholder="เช่น somchai">
                </div>
                <div>
                    <label class="text-xs font-semibold text-slate-600">ชื่อ-นามสกุล / ตำแหน่ง</label>
                    <input id="swal-name" class="w-full px-3 py-2 border rounded-xl text-sm" placeholder="เช่น สมชาย ช่างใจดี">
                </div>
                <div>
                    <label class="text-xs font-semibold text-slate-600">รหัสผ่าน (Password)</label>
                    <input type="password" id="swal-password" class="w-full px-3 py-2 border rounded-xl text-sm" placeholder="••••••••">
                </div>
                <div>
                    <label class="text-xs font-semibold text-slate-600">ระดับสิทธิ์ (Role)</label>
                    <select id="swal-role" class="w-full px-3 py-2 border rounded-xl text-sm">
                        <option value="owner">เจ้าของเพจ (Page Owner - โพสต์/ใช้ AI/วางแผน)</option>
                        <option value="staff">ทีมงาน (Staff - ร่างโพสต์/ดูตาราง)</option>
                        <option value="admin">ผู้ดูแลระบบ (Admin - จัดการทุกอย่าง)</option>
                    </select>
                </div>
            </div>
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: 'บันทึกผู้ใช้',
        cancelButtonText: 'ยกเลิก',
        confirmButtonColor: '#0B3B60',
        preConfirm: () => {
            return {
                username: document.getElementById('swal-username').value.trim(),
                name: document.getElementById('swal-name').value.trim(),
                password: document.getElementById('swal-password').value.trim(),
                role: document.getElementById('swal-role').value
            }
        }
    });

    if (formValues && formValues.username && formValues.password) {
        try {
            const res = await fetch('/api/admin/users', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(formValues)
            });
            const result = await res.json();
            if (result.success) {
                Swal.fire('สำเร็จ', 'เพิ่มผู้ใช้เรียบร้อยแล้ว', 'success');
                loadUsers();
            } else {
                Swal.fire('ผิดพลาด', result.error, 'error');
            }
        } catch (e) {
            Swal.fire('ข้อผิดพลาด', 'ไม่สามารถเพิ่มผู้ใช้ได้', 'error');
        }
    }
}

// Delete User
async function deleteUser(username) {
    const confirm = await Swal.fire({
        title: `ลบผู้ใช้ "${username}"?`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        confirmButtonText: 'ยืนยันลบ',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/admin/users/${username}`, { method: 'DELETE' });
        const result = await res.json();
        if (result.success) {
            loadUsers();
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'ลบผู้ใช้ไม่สำเร็จ', 'error');
    }
}


// ================= MULTI-PAGE SWITCHER FUNCTIONS =================

function togglePageDropdown() {
    const menu = document.getElementById('page-dropdown-menu');
    if (menu) menu.classList.toggle('hidden');
}

// Close dropdown on outside click
document.addEventListener('click', (e) => {
    const menu = document.getElementById('page-dropdown-menu');
    const btn = document.getElementById('current-page-label');
    if (menu && !menu.contains(e.target) && !e.target.closest('button[onclick="togglePageDropdown()"]')) {
        menu.classList.add('hidden');
    }
});

async function switchActivePage(pageId) {
    Swal.fire({
        title: 'กำลังสลับเพจ...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/pages/switch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ page_id: pageId })
        });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'สลับเพจสำเร็จ!',
                text: `กำลังจัดการเพจ: ${result.active_page.name}`,
                timer: 1500,
                showConfirmButton: false
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire('ข้อผิดพลาด', result.error, 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'ไม่สามารถสลับเพจได้', 'error');
    }
}

async function openSyncPagesModal() {
    const { value: token } = await Swal.fire({
        title: '🔑 ซิงค์ Token & ตั้งค่า .env อัตโนมัติ',
        html: `
            <div class="text-left text-xs text-slate-600 space-y-2">
                <p>วาง <strong>Access Token</strong> จาก Graph API Explorer (ใช้ได้ทั้ง User Token หรือ Page Token):</p>
                <p class="text-slate-500">ระบบจะดึงรายชื่อเพจทั้งหมดที่คุณดูแล ดึง Page Token ของทุกเพจ และ<strong>เขียนค่าลงไฟล์ .env ให้อัตโนมัติทันที</strong></p>
                <textarea id="swal-token" class="w-full px-3 py-2 border rounded-xl text-xs font-mono h-24 focus:ring-2 focus:ring-[#0B3B60] focus:outline-none" placeholder="วาง EAAQ... ตรงนี้"></textarea>
            </div>
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: '⚡ บันทึกใส่ .env & ซิงค์เพจ',
        cancelButtonText: 'ยกเลิก',
        confirmButtonColor: '#0B3B60',
        preConfirm: () => {
            const val = document.getElementById('swal-token').value.trim();
            if (!val) {
                Swal.showValidationMessage('กรุณาวาง Access Token');
                return false;
            }
            return val;
        }
    });

    if (token) {
        Swal.fire({
            title: 'กำลังเชื่อมต่อ Meta และอัปเดต .env...',
            allowOutsideClick: false,
            didOpen: () => { Swal.showLoading(); }
        });

        try {
            const res = await fetch('/api/pages/connect_token', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            });
            const result = await res.json();
            Swal.close();

            if (result.success) {
                const activeName = result.active_page ? result.active_page.name : 'FixPack';
                Swal.fire({
                    icon: 'success',
                    title: `ซิงค์สำเร็จ! (${result.count} เพจ)`,
                    html: `
                        <div class="text-left text-xs space-y-1">
                            <p>✅ อัปเดต <strong>FACEBOOK_PAGE_ID</strong> และ <strong>FACEBOOK_PAGE_ACCESS_TOKEN</strong> ในไฟล์ .env เรียบร้อยแล้ว</p>
                            <p>🎯 เพจที่เปิดใช้งานอยู่: <strong>${activeName}</strong></p>
                            <p class="text-slate-400 mt-2">* เมื่อคุณสลับเพจ ระบบจะอัปเดตไฟล์ .env ให้ตรงกับเพจใหม่ให้อัตโนมัติทุกครั้ง</p>
                        </div>
                    `,
                    confirmButtonColor: '#0B3B60'
                }).then(() => {
                    window.location.reload();
                });
            } else {
                Swal.fire('เกิดข้อผิดพลาด', result.error, 'error');
            }
        } catch (e) {
            Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อล้มเหลว', 'error');
        }
    }
}
