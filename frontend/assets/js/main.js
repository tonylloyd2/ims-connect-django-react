// Main JavaScript file

// API Configuration
const API_BASE_URL = 'https://147.93.136.124:8801'; // Removed /api since it's already in the URL paths

// Configure Axios defaults
axios.defaults.baseURL = API_BASE_URL;
axios.interceptors.request.use(function (config) {
    const token = localStorage.getItem('access_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    // Add debug logging
    console.log('Request Config:', {
        method: config.method,
        url: config.url,
        baseURL: config.baseURL,
        headers: config.headers
    });
    return config;
}, function (error) {
    console.error('Request Error:', error);
    return Promise.reject(error);
});

// Add response interceptor for debugging
axios.interceptors.response.use(function (response) {
    console.log('API Response:', response.config.method.toUpperCase(), response.config.url, response.status);
    return response;
}, function (error) {
    console.error('API Error:', error.config?.method.toUpperCase(), error.config?.url, error.response?.status);
    return Promise.reject(error);
});

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl)
    });

    // Check authentication and update UI
    const token = localStorage.getItem('access_token');
    if (token) {
        fetchUserProfile();
    } else {
        updateUIForLoggedOutUser();
    }

    // Event listeners
    $('#loginBtn').click(showLoginModal);
    $('#registerBtn').click(showRegisterModal);
    $('#logoutBtn').click(logout);

    // Initialize Select2 for all select elements with the select2 class
    initializeSelect2();
});

// Authentication Functions
function checkAuth() {
    const token = localStorage.getItem('access_token');
    if (token) {
        updateUIForLoggedInUser();
    } else {
        updateUIForLoggedOutUser();
    }
}

function showLoginModal() {
    const modalHtml = `
        <div class="modal fade" id="loginModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Login</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="loginForm">
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="loginEmail" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" class="form-control" id="loginPassword" required>
                            </div>
                            <button type="submit" class="btn btn-primary">Login</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;

    $('body').append(modalHtml);
    const loginModal = new bootstrap.Modal(document.getElementById('loginModal'));
    loginModal.show();

    $('#loginForm').on('submit', function(e) {
        e.preventDefault();
        handleLogin();
    });
}

function handleLogin() {
    const email = $('#loginEmail').val();
    const password = $('#loginPassword').val();

    // API call to login
    $.ajax({
        url: '/api/auth/login',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({ email, password }),
        success: function(response) {
            localStorage.setItem('access_token', response.token);
            localStorage.setItem('user', JSON.stringify(response.user));
            window.location.href = '/pages/dashboard.html';
        },
        error: function(xhr) {
            showError('Login failed. Please check your credentials.');
        }
    });
}

function showRegisterModal() {
    const modalHtml = `
        <div class="modal fade" id="registerModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Register</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <form id="registerForm">
                            <div class="mb-3">
                                <label class="form-label">First Name</label>
                                <input type="text" class="form-control" id="firstName" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Last Name</label>
                                <input type="text" class="form-control" id="lastName" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Email</label>
                                <input type="email" class="form-control" id="registerEmail" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Password</label>
                                <input type="password" class="form-control" id="registerPassword" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Department</label>
                                <select class="form-select" id="department" required>
                                    <option value="">Select Department</option>
                                    <option value="IT">IT</option>
                                    <option value="HR">HR</option>
                                    <option value="Finance">Finance</option>
                                    <option value="Marketing">Marketing</option>
                                </select>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Region</label>
                                <select class="form-select" id="region" required>
                                    <option value="">Select Region</option>
                                    <option value="North">North</option>
                                    <option value="South">South</option>
                                    <option value="East">East</option>
                                    <option value="West">West</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary">Register</button>
                        </form>
                    </div>
                </div>
            </div>
        </div>
    `;

    $('body').append(modalHtml);
    const registerModal = new bootstrap.Modal(document.getElementById('registerModal'));
    registerModal.show();

    $('#registerForm').on('submit', function(e) {
        e.preventDefault();
        handleRegistration();
    });
}

function handleRegistration() {
    const userData = {
        firstName: $('#firstName').val(),
        lastName: $('#lastName').val(),
        email: $('#registerEmail').val(),
        password: $('#registerPassword').val(),
        department: $('#department').val(),
        region: $('#region').val()
    };

    // API call to register
    $.ajax({
        url: '/api/auth/register',
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify(userData),
        success: function(response) {
            showSuccess('Registration successful! Please login.');
            $('#registerModal').modal('hide');
            showLoginModal();
        },
        error: function(xhr) {
            showError('Registration failed. Please try again.');
        }
    });
}

function logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    window.location.href = '/index.html';
}

// Category Functions
async function loadCategories(selectElement) {
    try {
        const response = await axios.get('/api/categories/');
        console.log('Categories loaded:', response.data);
        
        const select = $(selectElement);
        select.empty();
        select.append('<option value="">Select a category</option>');
        
        response.data.forEach(category => {
            select.append(`<option value="${category.id}">${category.name}</option>`);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
        showError('Failed to load categories. Please try again.');
    }
}

// Initialize Select2 for all select elements with the select2 class
function initializeSelect2() {
    $('.select2').select2({
        theme: 'bootstrap-5',
        width: '100%'
    });
}

// UI Update Functions
function updateUIForLoggedInUser() {
    try {
        const user = JSON.parse(localStorage.getItem('user'));
        if (user) {
            // Update user name in the header
            $('#userName').text(user.username || 'User');
            
            // Update profile dropdown
            const userInitial = (user.username || 'U')[0].toUpperCase();
            $('#userAvatar').text(userInitial);
            
            // Show authenticated nav items
            $('.auth-required').show();
            $('.no-auth-required').hide();
        } else {
            // If no user data, try to fetch it
            fetchUserProfile();
        }
    } catch (error) {
        console.error('Error updating UI for logged in user:', error);
    }
}

async function fetchUserProfile() {
    try {
        const response = await axios.get('/api/users/profile/');
        const userData = response.data;
        
        // Store user data
        localStorage.setItem('user', JSON.stringify(userData));
        
        // Update UI
        updateUIForLoggedInUser();
        
        return userData;
    } catch (error) {
        console.error('Error fetching user profile:', error);
        if (error.response?.status === 401) {
            // Token might be expired, redirect to login
            logout();
        }
    }
}

function updateUIForLoggedOutUser() {
    $('.auth-buttons').html(`
        <a href="#" class="btn btn-outline-light me-2" id="loginBtn">Login</a>
        <a href="#" class="btn btn-light" id="registerBtn">Register</a>
    `);
}

// Utility Functions
function showSuccess(message) {
    const toast = `
        <div class="toast align-items-center text-white bg-success border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    showToast(toast);
}

function showError(message) {
    const toast = `
        <div class="toast align-items-center text-white bg-danger border-0" role="alert">
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        </div>
    `;
    showToast(toast);
}

function showToast(toastHtml) {
    const toastContainer = document.getElementById('toastContainer') || createToastContainer();
    $(toastContainer).append(toastHtml);
    const toast = new bootstrap.Toast($('.toast').last());
    toast.show();
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toastContainer';
    container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
    document.body.appendChild(container);
    return container;
}
