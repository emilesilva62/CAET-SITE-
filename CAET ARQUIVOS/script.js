document.addEventListener('DOMContentLoaded', () => {
    if (document.getElementById('dashboard')) {
        showSection('dashboard');
        loadUserProfile();
        loadUserFiles();
        document.getElementById('profile-form').addEventListener('submit', handleProfileUpdate);
    } else {
        showSection('home');
        showTab('login');
        document.getElementById('login-form').addEventListener('submit', handleLogin);
        document.getElementById('register-form').addEventListener('submit', handleRegister);
        document.getElementById('upload-form').addEventListener('submit', handleUpload);
        document.getElementById('forgot-form').addEventListener('submit', handleForgotPassword);
        document.getElementById('upload-file').addEventListener('change', handlePreview);
    }
});

function showSection(sectionId) {
    document.querySelectorAll('.section').forEach(section => section.classList.remove('active'));
    document.getElementById(sectionId).classList.add('active');
}

function showTab(tabId) {
    document.querySelectorAll('.tab-panel').forEach(tab => tab.classList.remove('active'));
    document.getElementById(tabId).classList.add('active');
    document.querySelectorAll('.tab-link').forEach(link => link.parentElement.classList.remove('active'));
    event.target.parentElement.classList.add('active');
}

function toggleMenu() {
    document.querySelector('.nav-list').classList.toggle('active');
}

function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

function sanitizeInput(input) {
    return input.replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function showError(formId, errorDiv) {
    const form = document.getElementById(formId);
    const existingError = form.querySelector('.error');
    if (existingError) existingError.remove();
    form.appendChild(errorDiv);
}

function handleLogin(event) {
    event.preventDefault();
    const email = sanitizeInput(document.getElementById('login-email').value.trim().toLowerCase());
    const password = sanitizeInput(document.getElementById('login-password').value.trim());
    const csrfToken = document.getElementById('csrf-token-login').value;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.style.color = 'red';
    errorDiv.style.marginTop = '0.5rem';

    if (!email || !validateEmail(email)) {
        errorDiv.textContent = 'Por favor, insira um email válido.';
        showError('login-form', errorDiv);
        return;
    }
    if (!password) {
        errorDiv.textContent = 'Por favor, insira uma senha.';
        showError('login-form', errorDiv);
        return;
    }

    console.log('Tentativa de login:', { email, password, csrfToken });
    fetch('/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password, csrf_token: csrfToken })
    })
    .then(response => {
        console.log('Resposta do servidor:', response.status);
        return response.json();
    })
    .then(data => {
        if (data.success) {
            alert('Login bem-sucedido!');
            window.location.href = '/dashboard';
        } else {
            errorDiv.textContent = data.message || 'Erro no login.';
            showError('login-form', errorDiv);
        }
    })
    .catch(error => {
        console.error('Erro na requisição:', error);
        errorDiv.textContent = 'Erro ao conectar com o servidor.';
        showError('login-form', errorDiv);
    });
}

function handleRegister(event) {
    event.preventDefault();
    const name = sanitizeInput(document.getElementById('register-name').value.trim());
    const email = sanitizeInput(document.getElementById('register-email').value.trim());
    const password = document.getElementById('register-password').value;
    const confirmPassword = document.getElementById('register-confirm-password').value;
    const dob = document.getElementById('register-dob').value;
    const phone = sanitizeInput(document.getElementById('register-phone').value.trim());
    const csrfToken = document.getElementById('csrf-token-register').value;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.style.color = 'red';
    errorDiv.style.marginTop = '0.5rem';

    if (!name) {
        errorDiv.textContent = 'Por favor, insira seu nome.';
        showError('register-form', errorDiv);
        return;
    }
    if (!email || !validateEmail(email)) {
        errorDiv.textContent = 'Por favor, insira um email válido.';
        showError('register-form', errorDiv);
        return;
    }
    if (!password || password.length < 6) {
        errorDiv.textContent = 'A senha deve ter pelo menos 6 caracteres.';
        showError('register-form', errorDiv);
        return;
    }
    if (password !== confirmPassword) {
        errorDiv.textContent = 'As senhas não coincidem.';
        showError('register-form', errorDiv);
        return;
    }
    if (!dob) {
        errorDiv.textContent = 'Por favor, selecione sua data de nascimento.';
        showError('register-form', errorDiv);
        return;
    }
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) age--;
    if (age < 13) {
        errorDiv.textContent = 'Você deve ter pelo menos 13 anos.';
        showError('register-form', errorDiv);
        return;
    }
    if (!phone) {
        errorDiv.textContent = 'Por favor, insira um telefone.';
        showError('register-form', errorDiv);
        return;
    }
    const cleanPhone = phone.replace(/\D/g, '');
    if (!/^\d{10,11}$/.test(cleanPhone)) {
        errorDiv.textContent = 'Por favor, insira um telefone válido (10-11 dígitos).';
        showError('register-form', errorDiv);
        return;
    }

    fetch('/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, email, password, dob, phone, csrf_token: csrfToken })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Cadastro realizado com sucesso!');
            document.getElementById('register-form').reset();
            showTab('login');
        } else {
            errorDiv.textContent = data.message || 'Erro no cadastro.';
            showError('register-form', errorDiv);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Erro ao conectar com o servidor.';
        showError('register-form', errorDiv);
    });
}

function handleForgotPassword(event) {
    event.preventDefault();
    const email = sanitizeInput(document.getElementById('forgot-email').value.trim());
    const csrfToken = document.getElementById('csrf-token-forgot').value;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.style.color = 'red';
    errorDiv.style.marginTop = '0.5rem';

    if (!email || !validateEmail(email)) {
        errorDiv.textContent = 'Por favor, insira um email válido.';
        showError('forgot-form', errorDiv);
        return;
    }

    fetch('/forgot-password', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, csrf_token: csrfToken })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Email de recuperação enviado!');
        } else {
            errorDiv.textContent = data.message || 'Erro na solicitação.';
            showError('forgot-form', errorDiv);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Erro ao conectar com o servidor.';
        showError('forgot-form', errorDiv);
    });
}

function handleUpload(event) {
    event.preventDefault();
    const files = document.getElementById('upload-file').files;
    const csrfToken = document.getElementById('csrf-token-upload').value;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.style.color = 'red';
    errorDiv.style.marginTop = '0.5rem';

    if (!files.length) {
        errorDiv.textContent = 'Por favor, selecione pelo menos um arquivo.';
        showError('upload-form', errorDiv);
        return;
    }

    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    formData.append('csrf_token', csrfToken);

    fetch('/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Upload de ${files.length} arquivo(s) bem-sucedido!`);
            document.getElementById('upload-form').reset();
            if (window.location.pathname === '/dashboard') {
                loadUserFiles();
            }
        } else {
            errorDiv.textContent = data.message || 'Erro no upload.';
            showError('upload-form', errorDiv);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Erro ao conectar com o servidor.';
        showError('upload-form', errorDiv);
    });
}

function handlePreview(event) {
    const preview = document.getElementById('preview');
    preview.innerHTML = '';
    const files = event.target.files;

    for (let file of files) {
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const img = document.createElement('img');
                img.src = e.target.result;
                img.className = 'preview-img';
                preview.appendChild(img);
            };
            reader.readAsDataURL(file);
        } else {
            const p = document.createElement('p');
            p.textContent = `Arquivo: ${file.name}`;
            preview.appendChild(p);
        }
    }
}

function handleGoogleSignIn(response) {
    if (response.credential) {
        fetch('/google-login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ token: response.credential })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Login com Google bem-sucedido!');
                window.location.href = '/dashboard';
            } else {
                alert('Erro no login com Google: ' + data.message);
            }
        })
        .catch(error => {
            alert('Erro ao conectar com o servidor.');
        });
    }
}

function initMap() {
    const location = { lat: -23.5505, lng: -46.6333 };
    const map = new google.maps.Map(document.getElementById('map'), {
        zoom: 15,
        center: location,
        styles: [
            { elementType: 'geometry', stylers: [{ color: '#f5f5f5' }] },
            { elementType: 'labels.text.fill', stylers: [{ color: '#616161' }] },
            { elementType: 'labels.text.stroke', stylers: [{ color: '#f5f5f5' }] },
            { featureType: 'administrative.land_parcel', stylers: [{ visibility: 'off' }] },
            { featureType: 'administrative.neighborhood', stylers: [{ visibility: 'off' }] }
        ]
    });
    new google.maps.Marker({ position: location, map, title: 'CAET - São Paulo' });
}

function loadUserProfile() {
    fetch('/profile', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('profile-name').value = data.user.name;
            document.getElementById('profile-email').value = data.user.email;
            document.getElementById('profile-phone').value = data.user.phone;
            document.getElementById('profile-dob').value = data.user.dob;
        } else {
            alert('Erro ao carregar perfil: ' + data.message);
        }
    })
    .catch(error => {
        alert('Erro ao conectar com o servidor.');
    });
}

function handleProfileUpdate(event) {
    event.preventDefault();
    const name = sanitizeInput(document.getElementById('profile-name').value.trim());
    const phone = sanitizeInput(document.getElementById('profile-phone').value.trim());
    const dob = document.getElementById('profile-dob').value;
    const csrfToken = document.getElementById('csrf-token-profile').value;
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error';
    errorDiv.style.color = 'red';
    errorDiv.style.marginTop = '0.5rem';

    if (!name) {
        errorDiv.textContent = 'Por favor, insira seu nome.';
        showError('profile-form', errorDiv);
        return;
    }
    if (!dob) {
        errorDiv.textContent = 'Por favor, selecione sua data de nascimento.';
        showError('profile-form', errorDiv);
        return;
    }
    const birthDate = new Date(dob);
    const today = new Date();
    let age = today.getFullYear() - birthDate.getFullYear();
    const monthDiff = today.getMonth() - birthDate.getMonth();
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birthDate.getDate())) age--;
    if (age < 13) {
        errorDiv.textContent = 'Você deve ter pelo menos 13 anos.';
        showError('profile-form', errorDiv);
        return;
    }
    if (!phone) {
        errorDiv.textContent = 'Por favor, insira um telefone.';
        showError('profile-form', errorDiv);
        return;
    }
    const cleanPhone = phone.replace(/\D/g, '');
    if (!/^\d{10,11}$/.test(cleanPhone)) {
        errorDiv.textContent = 'Por favor, insira um telefone válido (10-11 dígitos).';
        showError('profile-form', errorDiv);
        return;
    }

    fetch('/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, phone, dob, csrf_token: csrfToken })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Perfil atualizado com sucesso!');
        } else {
            errorDiv.textContent = data.message || 'Erro ao atualizar perfil.';
            showError('profile-form', errorDiv);
        }
    })
    .catch(error => {
        errorDiv.textContent = 'Erro ao conectar com o servidor.';
        showError('profile-form', errorDiv);
    });
}

function loadUserFiles() {
    fetch('/files', {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' }
    })
    .then(response => response.json())
    .then(data => {
        const fileList = document.getElementById('file-list');
        fileList.innerHTML = '';
        if (data.success && data.files.length) {
            data.files.forEach(file => {
                const fileCard = document.createElement('div');
                fileCard.className = 'file-card';
                if (file.type.startsWith('image/')) {
                    fileCard.innerHTML = `
                        <img src="/uploads/${file.name}" alt="${file.name}">
                        <p>${file.name}</p>
                        <a href="/Uploads/${file.name}" download>Baixar</a>
                    `;
                } else {
                    fileCard.innerHTML = `
                        <p>${file.name}</p>
                        <a href="/Uploads/${file.name}" download>Baixar</a>
                    `;
                }
                fileList.appendChild(fileCard);
            });
        } else {
            fileList.innerHTML = '<p>Nenhum arquivo encontrado.</p>';
        }
    })
    .catch(error => {
        alert('Erro ao carregar arquivos.');
    });
}

function logout() {
    fetch('/logout', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ csrf_token: 'mock-csrf-token' })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Logout bem-sucedido!');
            window.location.href = '/';
        } else {
            alert('Erro ao fazer logout: ' + data.message);
        }
    })
    .catch(error => {
        alert('Erro ao conectar com o servidor.');
    });
}

window.onload = () => {
    if (document.getElementById('g_id_onload_login')) {
        google.accounts.id.initialize({
            client_id: "YOUR_GOOGLE_CLIENT_ID",
            callback: handleGoogleSignIn
        });
        google.accounts.id.renderButton(document.querySelector('#g_id_onload_login'), { theme: 'outline', size: 'large' });
        google.accounts.id.renderButton(document.querySelector('#g_id_onload_register'), { theme: 'outline', size: 'large', text: 'signup_with' });
    }
};