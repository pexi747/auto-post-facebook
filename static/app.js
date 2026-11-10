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
    if (tabId === 'planner') {
        loadUpcomingHolidays(60);
    }
    if (tabId === 'users') loadUsers();
    if (tabId === 'ci') {
        loadBrandConfigForm();
        loadBrandDocuments();
    }
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

    if (document.getElementById('brand-docs-container')) {
        loadBrandDocuments();
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
let currentAIGenImagePath = "";

// Update Image choice for Preview (AI Gen, Upload, Text Only)
function updateImageChoice(choice) {
    const previewImg = document.getElementById('preview-img');
    const previewContainer = document.getElementById('preview-image-container');
    const pathInput = document.getElementById('selected-image-path');
    const subAIGen = document.getElementById('subpanel-aigen');
    const subUpload = document.getElementById('subpanel-upload');
    const subNone = document.getElementById('subpanel-none');

    // Reset styles
    ['aigen', 'upload', 'none'].forEach(id => {
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
    if (subAIGen) subAIGen.classList.add('hidden');
    if (subUpload) subUpload.classList.add('hidden');
    if (subNone) subNone.classList.add('hidden');

    if (choice === 'aigen') {
        if (subAIGen) subAIGen.classList.remove('hidden');
        if (previewContainer) previewContainer.classList.remove('hidden');
        if (currentAIGenImagePath) {
            const displayUrl = currentAIGenImagePath.startsWith('/') ? currentAIGenImagePath : '/' + currentAIGenImagePath;
            if (previewImg) previewImg.src = displayUrl;
            if (pathInput) pathInput.value = currentAIGenImagePath;
        } else {
            if (previewImg) previewImg.src = '/static/cover.jpg';
            if (pathInput) pathInput.value = "";
        }
    } else if (choice === 'upload') {
        if (subUpload) subUpload.classList.remove('hidden');
        if (previewContainer) previewContainer.classList.remove('hidden');
        if (currentUploadedImagePath) {
            const displayUrl = currentUploadedImagePath.startsWith('/') ? currentUploadedImagePath : '/' + currentUploadedImagePath;
            if (previewImg) previewImg.src = displayUrl;
            if (pathInput) pathInput.value = currentUploadedImagePath;
            const visionRow = document.getElementById('upload-vision-ai-row');
            if (visionRow) visionRow.classList.remove('hidden');
        } else {
            if (previewImg) previewImg.src = '/static/cover.jpg';
            if (pathInput) pathInput.value = "";
        }
    } else { // none (text only)
        if (subNone) subNone.classList.remove('hidden');
        if (previewContainer) previewContainer.classList.add('hidden');
        if (pathInput) pathInput.value = "";
    }
}

// Generate photorealistic AI image based on caption & brand context
async function generateAIImageForPost() {
    const topic = document.getElementById('post-topic').value.trim() || 'ภาพบริการระดับมืออาชีพ';
    const caption = document.getElementById('post-caption').value.trim();
    const watermarkCheck = document.getElementById('aigen-watermark-checkbox');
    const applyWatermark = watermarkCheck ? watermarkCheck.checked : true;

    Swal.fire({
        title: '🎨 AI กำลังออกแบบและสร้างภาพประกอบ...',
        html: `
            <div class="space-y-2 text-xs text-slate-600 mt-2 text-left bg-slate-50 p-3 rounded-xl border border-slate-200">
                <p>1. วิเคราะห์บริบทแคปชั่นและ Brand DNA</p>
                <p>2. เรนเดอร์ภาพถ่ายโฆษณาคมชัดสูง (1024x1024 Commercial Quality)</p>
                ${applyWatermark ? '<p class="text-emerald-700 font-semibold">3. 🛡️ ประทับลายน้ำแบรนด์ป้องกันการคัดลอกรูปไปใช้</p>' : ''}
            </div>
        `,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/ai/generate_image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: topic,
                caption: caption,
                apply_watermark: applyWatermark
            })
        });
        const data = await res.json();
        Swal.close();

        if (data.success && data.image_path) {
            currentAIGenImagePath = data.image_path;
            const pathInput = document.getElementById('selected-image-path');
            if (pathInput) pathInput.value = data.image_path;

            const previewImg = document.getElementById('preview-img');
            if (previewImg) previewImg.src = data.url + '?t=' + Date.now();

            const thumbImg = document.getElementById('img-thumb-aigen');
            if (thumbImg) thumbImg.src = data.url + '?t=' + Date.now();

            const previewContainer = document.getElementById('preview-image-container');
            if (previewContainer) previewContainer.classList.remove('hidden');

            Swal.fire({
                icon: 'success',
                title: '✨ AI สร้างภาพประกอบสำเร็จ!',
                html: `
                    <div class="space-y-2 text-left text-xs">
                        <img src="${data.url}?t=${Date.now()}" class="w-full max-h-52 object-cover rounded-xl border border-slate-200 shadow-sm mb-2">
                        <p class="text-slate-700"><strong>ภาพถูกบันทึกและพร้อมโพสต์:</strong> เข้ากับเนื้อหาแคปชั่นเรียบร้อย</p>
                        ${applyWatermark ? '<div class="p-2.5 bg-emerald-50 text-emerald-800 rounded-lg border border-emerald-200 font-medium">🛡️ ปลอดภัย: ประทับลายน้ำแบรนด์เรียบร้อย ป้องกันการเอารูปไปใช้</div>' : ''}
                    </div>
                `,
                confirmButtonText: 'ยอดเยี่ยม ตกลง',
                confirmButtonColor: '#0B3B60'
            });
        } else {
            Swal.fire('เกิดข้อผิดพลาด', data.error || 'ไม่สามารถสร้างภาพได้ในขณะนี้', 'error');
        }
    } catch (err) {
        Swal.fire('เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', err.message, 'error');
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
    const wmCheck = document.getElementById('upload-watermark-checkbox');
    formData.append('watermark', (wmCheck && wmCheck.checked) ? 'true' : 'false');

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
                        const isHoliday = post.type === 'holiday_auto_scheduled' || post.holiday_id || post.holiday_name;
            const holidayBadge = isHoliday 
                ? `<span class="px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-700 font-bold text-xs border border-rose-200 flex items-center gap-1 shrink-0"><i class="fa-solid fa-cake-candles text-rose-500"></i> 🎉 วันสำคัญ: ${post.holiday_name || post.topic || 'เทศกาลวันสำคัญ'}</span>`
                : '';
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
                                ${holidayBadge}
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
    
    // Selected image (aigen, upload, or none)
    const selectedChoice = document.querySelector('input[name="image-choice"]:checked');
    const selectedImg = selectedChoice ? selectedChoice.value : 'aigen';
    let image_path = null;
    if (selectedImg === 'aigen') {
        image_path = document.getElementById('selected-image-path').value || currentAIGenImagePath || null;
    } else if (selectedImg === 'upload') {
        image_path = currentUploadedImagePath || null;
    } else {
        image_path = null; // none = text-only
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

// Helper: Color sync between picker and text input
function syncColorInput(type) {
    const picker = document.getElementById(`ci-${type}`);
    const text = document.getElementById(`ci-${type}-text`);
    if (picker && text) text.value = picker.value.toUpperCase();
}

function syncColorPicker(type) {
    const picker = document.getElementById(`ci-${type}`);
    const text = document.getElementById(`ci-${type}-text`);
    if (picker && text && text.value.startsWith('#') && (text.value.length === 7 || text.value.length === 4)) {
        picker.value = text.value;
    }
}

function setTonePreset(preset) {
    const toneInput = document.getElementById('ci-tone');
    if (toneInput) toneInput.value = preset;
}

// Load Brand Config into Form
async function loadBrandConfigForm() {
    try {
        const res = await fetch('/api/admin/brand');
        if (!res.ok) return;
        const brand = await res.json();

        if (document.getElementById('ci-name')) document.getElementById('ci-name').value = brand.brand_name || '';
        if (document.getElementById('ci-tagline')) document.getElementById('ci-tagline').value = brand.tagline || '';
        if (document.getElementById('ci-primary')) document.getElementById('ci-primary').value = brand.primary_color || '#0B3B60';
        if (document.getElementById('ci-primary-text')) document.getElementById('ci-primary-text').value = (brand.primary_color || '#0B3B60').toUpperCase();
        if (document.getElementById('ci-accent')) document.getElementById('ci-accent').value = brand.accent_color || '#FF5B00';
        if (document.getElementById('ci-accent-text')) document.getElementById('ci-accent-text').value = (brand.accent_color || '#FF5B00').toUpperCase();
        if (document.getElementById('ci-phone')) document.getElementById('ci-phone').value = brand.phone || '';
        if (document.getElementById('ci-price')) document.getElementById('ci-price').value = brand.price_tag || '';
        if (document.getElementById('ci-daily-time')) document.getElementById('ci-daily-time').value = brand.daily_post_time || '09:30';
        if (document.getElementById('ci-page-id')) document.getElementById('ci-page-id').value = brand.facebook_page_id || '';

        // Brand Identity & Story fields
        if (document.getElementById('ci-business-type')) document.getElementById('ci-business-type').value = brand.business_type || '';
        if (document.getElementById('ci-brand-story')) document.getElementById('ci-brand-story').value = brand.brand_story || '';
        if (document.getElementById('ci-target-audience')) document.getElementById('ci-target-audience').value = brand.target_audience || '';
        if (document.getElementById('ci-core-services')) document.getElementById('ci-core-services').value = brand.core_services || '';
        if (document.getElementById('ci-selling-points')) document.getElementById('ci-selling-points').value = brand.selling_points || '';
        if (document.getElementById('ci-tone')) document.getElementById('ci-tone').value = brand.tone_of_voice || '';
        if (document.getElementById('ci-negative')) document.getElementById('ci-negative').value = brand.negative_guidelines || '';
    } catch (e) {
        console.error('Error loading brand config:', e);
    }
}

// Save Brand Config (Admin)
async function saveBrandConfig(e) {
    e.preventDefault();
    const data = {
        brand_name: document.getElementById('ci-name') ? document.getElementById('ci-name').value : '',
        tagline: document.getElementById('ci-tagline') ? document.getElementById('ci-tagline').value : '',
        primary_color: document.getElementById('ci-primary') ? document.getElementById('ci-primary').value : '#0B3B60',
        accent_color: document.getElementById('ci-accent') ? document.getElementById('ci-accent').value : '#FF5B00',
        phone: document.getElementById('ci-phone') ? document.getElementById('ci-phone').value : '',
        price_tag: document.getElementById('ci-price') ? document.getElementById('ci-price').value : '',
        daily_post_time: document.getElementById('ci-daily-time') ? document.getElementById('ci-daily-time').value : '09:30',
        business_type: document.getElementById('ci-business-type') ? document.getElementById('ci-business-type').value : '',
        brand_story: document.getElementById('ci-brand-story') ? document.getElementById('ci-brand-story').value : '',
        target_audience: document.getElementById('ci-target-audience') ? document.getElementById('ci-target-audience').value : '',
        core_services: document.getElementById('ci-core-services') ? document.getElementById('ci-core-services').value : '',
        selling_points: document.getElementById('ci-selling-points') ? document.getElementById('ci-selling-points').value : '',
        tone_of_voice: document.getElementById('ci-tone') ? document.getElementById('ci-tone').value : '',
        negative_guidelines: document.getElementById('ci-negative') ? document.getElementById('ci-negative').value : ''
    };

    Swal.fire({
        title: 'กำลังบันทึกข้อมูล...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/admin/brand', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'บันทึกสำเร็จ!',
                text: 'บันทึกการตั้งค่า CI และตัวตนแบรนด์เรียบร้อยแล้ว',
                timer: 1500,
                showConfirmButton: false
            });
        } else {
            Swal.fire('ข้อผิดพลาด', result.error || 'บันทึกไม่สำเร็จ', 'error');
        }
    } catch (err) {
        Swal.fire('ข้อผิดพลาด', 'บันทึกไม่สำเร็จ ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
    }
}

// ================= BRAND KNOWLEDGE DOCUMENTS JS =================

async function loadBrandDocuments() {
    const container = document.getElementById('brand-docs-container');
    if (!container) return;

    try {
        const res = await fetch('/api/brand/documents');
        const data = await res.json();
        const docs = data.documents || [];

        if (docs.length === 0) {
            container.innerHTML = `
                <div class="text-center py-6 bg-slate-50/60 rounded-xl border border-slate-200">
                    <p class="text-xs text-slate-400">ยังไม่มีเอกสารแนบสำหรับเพจนี้ (สามารถแนบ PDF, Word, รูปภาพเมนู/โบรชัวร์ ด้านบนได้เลย)</p>
                </div>
            `;
            return;
        }

        container.innerHTML = docs.map(doc => {
            const ext = doc.filename.split('.').pop().toLowerCase();
            let iconClass = 'fa-file-lines text-slate-500';
            if (ext === 'pdf') iconClass = 'fa-file-pdf text-red-500';
            else if (['doc', 'docx'].includes(ext)) iconClass = 'fa-file-word text-blue-500';
            else if (['jpg', 'jpeg', 'png', 'webp'].includes(ext)) iconClass = 'fa-file-image text-purple-500';
            else if (['csv', 'xlsx', 'xls'].includes(ext)) iconClass = 'fa-file-excel text-emerald-500';

            return `
                <div class="bg-white p-3.5 rounded-xl border border-slate-200 flex items-start justify-between gap-3 shadow-xs hover:border-slate-300 transition">
                    <div class="flex items-start gap-3 min-w-0">
                        <div class="w-10 h-10 rounded-xl bg-slate-100 flex items-center justify-center shrink-0 text-xl">
                            <i class="fa-solid ${iconClass}"></i>
                        </div>
                        <div class="min-w-0">
                            <h4 class="text-xs font-bold text-slate-800 truncate" title="${doc.filename}">${doc.filename}</h4>
                            <div class="flex items-center gap-2 text-[10px] text-slate-400 mt-0.5">
                                <span><i class="fa-solid fa-hard-drive"></i> ${doc.size}</span>
                                <span>•</span>
                                <span><i class="fa-regular fa-clock"></i> ${doc.uploaded_at}</span>
                                <span>•</span>
                                <span class="text-emerald-600 font-semibold"><i class="fa-solid fa-check"></i> สกัดข้อความแล้ว (${doc.text_length} ตัวอักษร)</span>
                            </div>
                            <p class="text-[11px] text-slate-500 line-clamp-1 mt-1 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
                                💡 ${doc.summary || 'ไม่มีข้อความสรุป'}
                            </p>
                        </div>
                    </div>
                    <button type="button" onclick="deleteBrandDocument('${doc.id}')" class="p-2 text-slate-400 hover:text-red-500 rounded-lg hover:bg-red-50 transition shrink-0" title="ลบเอกสาร">
                        <i class="fa-solid fa-trash-can"></i>
                    </button>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<div class="p-3 text-center text-xs text-red-500">เกิดข้อผิดพลาดในการโหลดเอกสาร: ${e}</div>`;
    }
}

async function handleBrandDocUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    if (file.size > 20 * 1024 * 1024) {
        Swal.fire('ขนาดไฟล์ใหญ่เกินไป', 'ขนาดไฟล์สูงสุดไม่เกิน 20 MB', 'warning');
        return;
    }

    const formData = new FormData();
    formData.append('file', file);

    Swal.fire({
        title: 'กำลังอัปโหลดและสกัดข้อความ...',
        html: `กำลังอ่านข้อมูลจากไฟล์ <strong>${file.name}</strong> เพื่อบันทึกเข้าฐานความรู้ของแบรนด์...`,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/brand/documents/upload', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        Swal.close();

        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'อัปโหลดสำเร็จ!',
                text: `สกัดข้อความจากเอกสาร ${data.document.filename} เรียบร้อยแล้ว`,
                timer: 1500,
                showConfirmButton: false
            });
            loadBrandDocuments();
            // Reset input
            e.target.value = '';
        } else {
            Swal.fire('ข้อผิดพลาด', data.error || 'อัปโหลดล้มเหลว', 'error');
        }
    } catch (err) {
        Swal.fire('ข้อผิดพลาด', 'ไม่สามารถเชื่อมต่อเซิร์ฟเวอร์ได้', 'error');
    }
}

async function deleteBrandDocument(docId) {
    const confirm = await Swal.fire({
        title: 'ยืนยันการลบไฟล์เอกสารนี้?',
        text: 'เมื่อลบแล้ว AI จะไม่สามารถเข้าถึงข้อมูลจากเอกสารนี้ได้อีก',
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#e11d48',
        cancelButtonColor: '#64748b',
        confirmButtonText: 'ลบไฟล์',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/brand/documents/${docId}`, { method: 'DELETE' });
        const data = await res.json();
        if (data.success) {
            Swal.fire({
                icon: 'success',
                title: 'ลบเอกสารเรียบร้อยแล้ว',
                timer: 1200,
                showConfirmButton: false
            });
            loadBrandDocuments();
        } else {
            Swal.fire('ข้อผิดพลาด', 'ไม่สามารถลบเอกสารได้', 'error');
        }
    } catch (err) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อล้มเหลว', 'error');
    }
}

async function analyzeBrandDocumentsWithAI() {
    const activeName = document.getElementById('current-page-label') ? document.getElementById('current-page-label').textContent : 'เพจ';
    const confirm = await Swal.fire({
        title: 'ให้ AI สรุปข้อมูลจากเอกสารเข้า Brand DNA?',
        html: `AI จะอ่านข้อความจากทุกไฟล์ที่แนบไว้สำหรับเพจ <strong>${activeName}</strong> แล้วนำข้อมูลมาเติมลงในช่อง <strong>เรื่องราวแบรนด์, สินค้า/บริการหลัก, จุดเด่น, กลุ่มเป้าหมาย</strong> ให้อัตโนมัติ`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#7c3aed',
        cancelButtonColor: '#64748b',
        confirmButtonText: '✨ ให้ AI เริ่มวิเคราะห์',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    Swal.fire({
        title: 'AI กำลังวิเคราะห์เอกสารทั้งหมด...',
        html: 'กำลังสกัดอัตลักษณ์แบรนด์ เรื่องราว ความเป็นมา และรายการสินค้า/บริการ...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/brand/documents/analyze', { method: 'POST' });
        const result = await res.json();
        Swal.close();

        if (result.success && result.brand_dna) {
            const dna = result.brand_dna;
            // Fill into form fields
            if (dna.brand_name && document.getElementById('ci-name')) document.getElementById('ci-name').value = dna.brand_name;
            if (dna.tagline && document.getElementById('ci-tagline')) document.getElementById('ci-tagline').value = dna.tagline;
            if (dna.business_type && document.getElementById('ci-business-type')) document.getElementById('ci-business-type').value = dna.business_type;
            if (dna.brand_story && document.getElementById('ci-brand-story')) document.getElementById('ci-brand-story').value = dna.brand_story;
            if (dna.target_audience && document.getElementById('ci-target-audience')) document.getElementById('ci-target-audience').value = dna.target_audience;
            if (dna.core_services && document.getElementById('ci-core-services')) {
                document.getElementById('ci-core-services').value = Array.isArray(dna.core_services) ? dna.core_services.join('\n') : dna.core_services;
            }
            if (dna.selling_points && document.getElementById('ci-selling-points')) {
                document.getElementById('ci-selling-points').value = Array.isArray(dna.selling_points) ? dna.selling_points.join('\n') : dna.selling_points;
            }
            if (dna.tone_of_voice && document.getElementById('ci-tone')) document.getElementById('ci-tone').value = dna.tone_of_voice;
            if (dna.negative_guidelines && document.getElementById('ci-negative')) document.getElementById('ci-negative').value = dna.negative_guidelines;
            if (dna.phone && document.getElementById('ci-phone')) document.getElementById('ci-phone').value = dna.phone;
            if (dna.price_tag && document.getElementById('ci-price')) document.getElementById('ci-price').value = dna.price_tag;

            Swal.fire({
                icon: 'success',
                title: 'สกัดข้อมูลเข้า Brand DNA สำเร็จ!',
                html: `
                    <div class="text-left text-xs space-y-1 p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <p><strong>🎯 ธุรกิจ:</strong> ${dna.business_type || '-'}</p>
                        <p><strong>📖 เรื่องราว:</strong> ${(dna.brand_story || '-').substring(0, 100)}...</p>
                        <p><strong>👥 กลุ่มเป้าหมาย:</strong> ${dna.target_audience || '-'}</p>
                        <p class="text-purple-700 font-semibold mt-2">✨ ข้อมูลถูกเติมลงในฟอร์มด้านบนเรียบร้อยแล้ว คุณสามารถตรวจสอบและปรับแต่งเพิ่มเติมก่อนกดบันทึก</p>
                    </div>
                `,
                confirmButtonColor: '#7c3aed'
            });
        } else {
            Swal.fire('ข้อผิดพลาด', result.error || 'ไม่สามารถวิเคราะห์เอกสารได้', 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
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


async function learnBrandNow() {
    const activeName = document.getElementById('current-page-label') ? document.getElementById('current-page-label').textContent : 'เพจ';
    const confirm = await Swal.fire({
        title: `ให้ AI ศึกษาข้อมูลแบรนด์ "${activeName}" ใหม่?`,
        html: `ระบบจะดึงข้อมูลเกี่ยวกับเพจ คำอธิบาย หมวดหมู่ และโพสต์ล่าสุดจาก Facebook เพื่อสกัดอัตลักษณ์ (Brand DNA) กลุ่มเป้าหมาย จุดเด่น และโทนเสียงให้อัตโนมัติ`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#0B3B60',
        cancelButtonColor: '#64748b',
        confirmButtonText: '🧠 เริ่มให้ AI ศึกษาข้อมูล',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    Swal.fire({
        title: 'กำลังสแกนและศึกษาข้อมูลเพจ...',
        html: 'AI กำลังวิเคราะห์ข้อมูลเพจและโพสต์จาก Facebook เพื่อปรับแนวทางการคิดคอนเทนต์...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/brand/learn_now', { method: 'POST' });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'AI ศึกษาข้อมูลแบรนด์สำเร็จ!',
                html: `
                    <div class="text-left text-xs space-y-1.5 p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <p><strong>🎯 ประเภทธุรกิจ:</strong> ${result.brand_dna.business_type || '-'}</p>
                        <p><strong>👥 กลุ่มเป้าหมาย:</strong> ${result.brand_dna.target_audience || '-'}</p>
                        <p><strong>🗣️ โทนเสียง:</strong> ${result.brand_dna.tone_of_voice || '-'}</p>
                        <p class="text-emerald-600 font-semibold mt-2">✅ AI พร้อมคิดคอนเทนต์และวิเคราะห์รูปภาพตรงตามแบรนด์นี้แล้ว!</p>
                    </div>
                `,
                confirmButtonColor: '#0B3B60'
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire('ข้อผิดพลาด', result.error || 'ไม่สามารถวิเคราะห์เพจได้', 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

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

// ================= THAI HOLIDAYS FRONTEND LOGIC =================

async function loadUpcomingHolidays(daysAhead = 60) {
    const container = document.getElementById('holidays-container');
    if (!container) return;

    container.innerHTML = `
        <div class="col-span-full text-center py-10 bg-white/70 rounded-xl border border-dashed border-rose-200">
            <i class="fa-solid fa-spinner fa-spin text-2xl text-rose-500 mb-2"></i>
            <p class="text-xs text-slate-500">กำลังโหลดรายการวันสำคัญในช่วง ${daysAhead} วัน...</p>
        </div>
    `;

    try {
        const res = await fetch(`/api/holidays/upcoming?days_ahead=${daysAhead}`);
        const data = await res.json();

        if (!data.success || !data.holidays || data.holidays.length === 0) {
            container.innerHTML = `
                <div class="col-span-full text-center py-8 bg-white rounded-xl border border-slate-200 text-slate-500 text-xs">
                    ไม่พบวันสำคัญหรือเทศกาลในช่วง ${daysAhead} วันข้างหน้า
                </div>
            `;
            return;
        }

        container.innerHTML = data.holidays.map(h => {
            const isScheduled = h.is_scheduled === true;
            const daysUntil = h.days_until;
            let countdownBadge = '';
            if (daysUntil === 0) {
                countdownBadge = '<span class="px-2 py-0.5 rounded-full bg-rose-600 text-white font-bold text-[10px] animate-pulse">วันนี้!</span>';
            } else if (daysUntil === 1) {
                countdownBadge = '<span class="px-2 py-0.5 rounded-full bg-amber-500 text-white font-bold text-[10px]">พรุ่งนี้</span>';
            } else {
                countdownBadge = `<span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-medium text-[10px]">อีก ${daysUntil} วัน</span>`;
            }

            let typeBadgeClass = 'bg-blue-50 text-blue-700 border-blue-200';
            if (h.type === 'buddhist') typeBadgeClass = 'bg-amber-50 text-amber-700 border-amber-200';
            if (h.type === 'festival') typeBadgeClass = 'bg-rose-50 text-rose-700 border-rose-200';
            if (h.type === 'national_holiday') typeBadgeClass = 'bg-purple-50 text-purple-700 border-purple-200';

            return `
                <div class="bg-white p-4 sm:p-5 rounded-2xl border ${isScheduled ? 'border-emerald-300 shadow-sm bg-emerald-50/20' : 'border-slate-200 shadow-xs hover:border-rose-300 hover:shadow-sm'} flex flex-col justify-between transition gap-3">
                    <div>
                        <div class="flex items-center justify-between gap-2 mb-2">
                            <span class="text-[11px] font-semibold px-2 py-0.5 rounded-md border ${typeBadgeClass}">
                                ${h.category || 'วันสำคัญ'}
                            </span>
                            ${countdownBadge}
                        </div>
                        <h4 class="font-bold text-slate-800 text-sm sm:text-base leading-snug">
                            ${h.name}
                        </h4>
                        <div class="text-xs font-medium text-[#0B3B60] mt-1 flex items-center gap-1.5">
                            <i class="fa-regular fa-calendar text-rose-500"></i>
                            <span>${h.formatted_date_th || h.date}</span>
                        </div>
                        <p class="text-xs text-slate-500 mt-2 line-clamp-2 leading-relaxed">
                            ${h.description || h.greeting || ''}
                        </p>
                    </div>

                    <!-- Action Status -->
                    <div class="pt-3 border-t border-slate-100 mt-auto">
                        ${isScheduled ? `
                            <div class="flex items-center justify-between gap-2">
                                <span class="text-xs font-bold text-emerald-700 flex items-center gap-1">
                                    <i class="fa-solid fa-circle-check"></i> ตั้งเวลาโพสต์แล้ว
                                </span>
                                <button onclick="switchTab('calendar')" class="text-[11px] text-[#0B3B60] hover:underline font-semibold flex items-center gap-1">
                                    ดูในตาราง <i class="fa-solid fa-arrow-right text-[9px]"></i>
                                </button>
                            </div>
                        ` : `
                            <button onclick="scheduleSingleHoliday('${h.id}')" 
                                    class="w-full py-2 px-3 bg-rose-50 hover:bg-rose-600 hover:text-white text-rose-700 text-xs font-bold rounded-xl border border-rose-200 transition flex items-center justify-center gap-1.5 shadow-xs">
                                <i class="fa-solid fa-wand-magic-sparkles text-amber-500"></i> ให้ AI สร้าง & ตั้งเวลาโพสต์
                            </button>
                        `}
                    </div>
                </div>
            `;
        }).join('');

    } catch (e) {
        container.innerHTML = `<div class="col-span-full p-4 text-center text-red-500 text-xs">เกิดข้อผิดพลาดในการโหลดวันสำคัญ: ${e}</div>`;
    }
}

async function scheduleSingleHoliday(holidayId) {
    Swal.fire({
        title: '🤖 AI กำลังสร้างโพสต์วันสำคัญ...',
        html: `
            <div class="text-xs text-slate-600 space-y-1.5 text-left bg-slate-50 p-3 rounded-xl border border-slate-200">
                <p>1. วิเคราะห์ความหมายของวันสำคัญและ Brand DNA</p>
                <p>2. เขียนแคปชั่นอวยพรอันอบอุ่น พร้อม Call to Action และแฮชแท็ก</p>
                <p>3. 🎨 สร้างภาพประกอบ AI คมชัดระดับสต็อก 1024x1024</p>
                <p>4. 🛡️ ประทับตราลายน้ำแบรนด์ป้องกันการคัดลอกรูปภาพ</p>
            </div>
        `,
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/holidays/schedule_single', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ holiday_id: holidayId, auto_image: true })
        });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: 'ตั้งเวลาโพสต์สำเร็จ!',
                html: `
                    <div class="text-xs text-left space-y-1 p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-900">
                        <p><strong>🎉 วันสำคัญ:</strong> ${result.holiday.name}</p>
                        <p><strong>📅 กำหนดโพสต์:</strong> ${result.post.date} เวลา ${result.post.time} น.</p>
                        <p><strong>📝 หัวข้อ:</strong> ${result.post.topic}</p>
                    </div>
                `,
                confirmButtonColor: '#0B3B60'
            });
            loadUpcomingHolidays(60);
            loadPosts();
        } else {
            Swal.fire('เกิดข้อผิดพลาด', result.error || 'ไม่สามารถตั้งเวลาได้', 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

async function autoScheduleAllHolidays() {
    const confirm = await Swal.fire({
        title: '✨ รันระบบ AI วันสำคัญอัตโนมัติ?',
        html: `
            <div class="text-xs text-slate-600 space-y-2 text-left">
                <p>ระบบจะค้นหาวันสำคัญและเทศกาลทั้งหมดใน <strong>60 วันข้างหน้า</strong> ที่ยังไม่ได้ตั้งเวลา</p>
                <p>จากนั้น AI จะเขียนแคปชั่นตาม Brand DNA และสร้างภาพประกอบพร้อมลายน้ำแบรนด์ให้ครบทุกวันสำคัญในคลิกเดียว!</p>
            </div>
        `,
        icon: 'question',
        showCancelButton: true,
        confirmButtonColor: '#FF5B00',
        cancelButtonColor: '#64748b',
        confirmButtonText: '🚀 ให้ AI ดำเนินการทันที',
        cancelButtonText: 'ยกเลิก'
    });
    if (!confirm.isConfirmed) return;

    Swal.fire({
        title: '✨ AI กำลังสร้างและตั้งเวลาโพสต์วันสำคัญทั้งหมด...',
        html: 'กระบวนการนี้อาจใช้เวลาสักครู่ในการประมวลผลข้อความและภาพ AI คุณภาพสูง...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/holidays/auto_schedule_all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ days_ahead: 60, auto_image: true })
        });
        const result = await res.json();
        Swal.close();

        if (result.success) {
            Swal.fire({
                icon: 'success',
                title: `ตั้งเวลาโพสต์สำเร็จ (${result.scheduled_count} รายการ)!`,
                html: `
                    <p class="text-xs text-slate-600">
                        สร้างและบรรจุโพสต์วันสำคัญลงในตารางโพสต์ของเพจ <strong>${result.page_name}</strong> เรียบร้อยแล้ว
                    </p>
                `,
                confirmButtonColor: '#0B3B60'
            });
            loadUpcomingHolidays(60);
            loadPosts();
        } else {
            Swal.fire('เกิดข้อผิดพลาด', result.error || 'ไม่สามารถดำเนินการได้', 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

// ================= WALLET & CREDIT MANAGEMENT FRONTEND =================

let currentTopupPackageId = null;
let currentDiscoveredPages = [];

async function loadUserCreditBalance() {
    try {
        const res = await fetch('/api/credits/balance');
        const data = await res.json();
        if (data.success) {
            const balanceStr = data.unlimited ? '∞ (Admin)' : (data.credits || 0).toLocaleString();
            
            const headerBadge = document.getElementById('header-credit-balance');
            if (headerBadge) headerBadge.textContent = balanceStr;

            const walletDisplay = document.getElementById('wallet-balance-display');
            if (walletDisplay) walletDisplay.textContent = balanceStr;

            renderWalletTransactions(data.transactions || []);
        }
    } catch (e) {
        console.warn('Error loading credit balance:', e);
    }
}

function renderWalletTransactions(txs) {
    const tbody = document.getElementById('wallet-transactions-tbody');
    if (!tbody) return;

    if (txs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="py-8 text-center text-slate-400">
                    <i class="fa-solid fa-receipt text-2xl mb-2 text-slate-300"></i>
                    <p>ยังไม่มีประวัติการทำรายการ</p>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = txs.map(t => {
        const isPlus = t.amount > 0;
        const amountClass = isPlus ? 'text-emerald-600 font-bold' : 'text-rose-600 font-bold';
        const sign = isPlus ? '+' : '';

        let badgeType = '<span class="px-2 py-0.5 rounded-full bg-slate-100 text-slate-600 font-semibold text-[10px]">ใช้งานระบบ</span>';
        if (t.tx_type === 'welcome') {
            badgeType = '<span class="px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 font-bold text-[10px]">🎁 ต้อนรับสมาชิก</span>';
        } else if (t.tx_type === 'topup') {
            badgeType = '<span class="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700 font-bold text-[10px]">💳 เติมเงิน</span>';
        } else if (t.tx_type === 'admin_adjust') {
            badgeType = '<span class="px-2 py-0.5 rounded-full bg-purple-100 text-purple-700 font-bold text-[10px]">👑 ผู้ดูแลปรับยอด</span>';
        }

        return `
            <tr class="hover:bg-slate-50 transition">
                <td class="py-3 px-4 text-slate-500">${t.timestamp}</td>
                <td class="py-3 px-4">${badgeType}</td>
                <td class="py-3 px-4 text-slate-700 font-medium">${t.description || t.action}</td>
                <td class="py-3 px-4 text-right ${amountClass}">${sign}${t.amount}</td>
                <td class="py-3 px-4 text-right text-slate-800 font-bold">${t.balance_after !== undefined ? t.balance_after : '-'}</td>
            </tr>
        `;
    }).join('');
}

async function openTopupModal(packageId) {
    currentTopupPackageId = packageId;
    const modal = document.getElementById('modal-topup-qr');
    const qrContainer = document.getElementById('topup-qrcode-canvas');
    if (!modal || !qrContainer) return;

    qrContainer.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-2xl text-orange-500"></i>';
    modal.classList.remove('hidden');

    try {
        const res = await fetch('/api/credits/generate_qr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ package_id: packageId })
        });
        const data = await res.json();

        if (data.success) {
            document.getElementById('topup-pkg-name').textContent = data.package.name;
            document.getElementById('topup-pkg-price').textContent = data.package.price_thb;
            document.getElementById('topup-pkg-credits').textContent = data.package.credits;

            qrContainer.innerHTML = '';
            if (typeof QRCode !== 'undefined') {
                new QRCode(qrContainer, {
                    text: data.qr_payload,
                    width: 170,
                    height: 170,
                    colorDark: "#0B3B60",
                    colorLight: "#ffffff",
                    correctLevel: QRCode.CorrectLevel.M
                });
            } else {
                qrContainer.innerHTML = `<p class="text-xs text-slate-600 break-all p-2 font-mono">${data.qr_payload}</p>`;
            }
        } else {
            qrContainer.innerHTML = `<p class="text-xs text-red-500 p-4">${data.detail || 'ไม่สามารถสร้าง QR ได้'}</p>`;
        }
    } catch (e) {
        qrContainer.innerHTML = `<p class="text-xs text-red-500 p-4">เชื่อมต่อเซิร์ฟเวอร์ขัดข้อง: ${e}</p>`;
    }
}

function closeTopupModal() {
    const modal = document.getElementById('modal-topup-qr');
    if (modal) modal.classList.add('hidden');
}

async function confirmDemoTopup() {
    if (!currentTopupPackageId) return;

    Swal.fire({
        title: 'กำลังตรวจสอบการชำระเงิน...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/credits/topup_instant', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ package_id: currentTopupPackageId })
        });
        const data = await res.json();
        Swal.close();

        if (data.success) {
            closeTopupModal();
            Swal.fire({
                icon: 'success',
                title: 'เติมเครดิตสำเร็จ!',
                html: `
                    <div class="text-left text-xs space-y-1.5 p-3 bg-slate-50 rounded-xl border border-slate-200">
                        <p>🎉 ยอดเครดิตที่ได้รับ: <strong>+${data.added} เครดิต</strong></p>
                        <p>🪙 ยอดเครดิตคงเหลือใหม่: <strong>${data.balance} เครดิต</strong></p>
                    </div>
                `,
                confirmButtonColor: '#0B3B60'
            });
            loadUserCreditBalance();
        } else {
            Swal.fire('เกิดข้อผิดพลาด', data.error || 'ไม่สามารถเติมเครดิตได้', 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

// ================= CUSTOMER FACEBOOK PAGE LINKING =================

function openCustomerLinkFacebookModal() {
    const modal = document.getElementById('modal-customer-link-fb');
    if (!modal) return;
    document.getElementById('fb-link-step-1').classList.remove('hidden');
    document.getElementById('fb-link-step-2').classList.add('hidden');
    document.getElementById('customer-fb-token-input').value = '';
    modal.classList.remove('hidden');
}

function closeCustomerLinkFacebookModal() {
    const modal = document.getElementById('modal-customer-link-fb');
    if (modal) modal.classList.add('hidden');
}

function backToStep1FBLoing() {
    document.getElementById('fb-link-step-1').classList.remove('hidden');
    document.getElementById('fb-link-step-2').classList.add('hidden');
}

async function fetchCustomerPagesFromToken() {
    const tokenInput = document.getElementById('customer-fb-token-input');
    const token = tokenInput ? tokenInput.value.strip ? tokenInput.value.strip() : tokenInput.value.trim() : '';
    if (!token) {
        Swal.fire('กรุณากรอก Token', 'โปรดวาง User Access Token ของคุณก่อนดำเนินการ', 'warning');
        return;
    }

    const btn = document.getElementById('btn-fetch-customer-pages');
    if (btn) btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> กำลังตรวจสอบเพจของคุณ...';

    try {
        const res = await fetch('/api/customer/facebook/fetch_pages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ user_token: token })
        });
        const data = await res.json();
        if (btn) btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> ค้นหาเพจที่ฉันดูแล';

        if (data.success && data.pages && data.pages.length > 0) {
            currentDiscoveredPages = data.pages;
            const container = document.getElementById('discovered-pages-list');
            container.innerHTML = data.pages.map(p => `
                <label class="flex items-center gap-3 p-2.5 rounded-xl bg-white hover:bg-slate-100 border border-slate-200 cursor-pointer transition">
                    <input type="checkbox" name="selected_fb_pages" value="${p.id}" checked 
                           class="w-4 h-4 text-blue-600 rounded border-slate-300 focus:ring-blue-500">
                    <img src="${p.picture_url || '/static/profile.jpg'}" class="w-8 h-8 rounded-lg object-cover border border-slate-200" onerror="this.src='/static/profile.jpg'">
                    <div class="truncate flex-1 text-xs">
                        <div class="font-bold text-slate-800 truncate">${p.name}</div>
                        <div class="text-[10px] text-slate-400">ID: ${p.id} • ${p.category}</div>
                    </div>
                </label>
            `).join('');

            document.getElementById('fb-link-step-1').classList.add('hidden');
            document.getElementById('fb-link-step-2').classList.remove('hidden');
        } else {
            Swal.fire('ไม่พบเพจ', data.error || 'ไม่พบเพจที่บัญชีนี้เป็นผู้ดูแล หรือสิทธิ์ Token ไม่เพียงพอ', 'error');
        }
    } catch (e) {
        if (btn) btn.innerHTML = '<i class="fa-solid fa-magnifying-glass"></i> ค้นหาเพจที่ฉันดูแล';
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อ Facebook API ล้มเหลว', 'error');
    }
}

function selectAllDiscoveredPages(checked) {
    document.querySelectorAll('input[name="selected_fb_pages"]').forEach(cb => {
        cb.checked = checked;
    });
}

async function confirmImportSelectedPages() {
    const token = document.getElementById('customer-fb-token-input').value.trim();
    const selectedBoxes = Array.from(document.querySelectorAll('input[name="selected_fb_pages"]:checked'));
    if (selectedBoxes.length === 0) {
        Swal.fire('กรุณาเลือกเพจ', 'โปรดเลือกอย่างน้อย 1 เพจที่ต้องการนำเข้า', 'warning');
        return;
    }

    const selectedIds = selectedBoxes.map(b => b.value);

    Swal.fire({
        title: 'กำลังนำเข้าเพจของคุณ...',
        allowOutsideClick: false,
        didOpen: () => { Swal.showLoading(); }
    });

    try {
        const res = await fetch('/api/customer/facebook/import_pages', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                user_token: token,
                page_ids: selectedIds
            })
        });
        const data = await res.json();
        Swal.close();

        if (data.success) {
            closeCustomerLinkFacebookModal();
            Swal.fire({
                icon: 'success',
                title: `นำเข้าเพจสำเร็จ (${data.count} เพจ)!`,
                text: 'ระบบได้เชื่อมต่อเพจ Facebook เข้าสู่บัญชีของคุณเรียบร้อยแล้ว',
                confirmButtonColor: '#0B3B60'
            }).then(() => {
                window.location.reload();
            });
        } else {
            Swal.fire('เกิดข้อผิดพลาด', data.error || 'ไม่สามารถนำเข้าเพจได้', 'error');
        }
    } catch (e) {
        Swal.fire('ข้อผิดพลาด', 'เชื่อมต่อเซิร์ฟเวอร์ล้มเหลว', 'error');
    }
}

// Global hook: load credit balance on document ready
document.addEventListener('DOMContentLoaded', () => {
    loadUserCreditBalance();
});
