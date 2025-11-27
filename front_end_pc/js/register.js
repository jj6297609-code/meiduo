// 在 register.js 最前面添加
window.addEventListener('error', function (e) {
    console.log('全局错误捕获:', e);
    console.log('错误信息:', e.message);
    console.log('错误文件:', e.filename);
    console.log('错误行号:', e.lineno);
});

window.addEventListener('unhandledrejection', function (e) {
    console.log('未处理的 Promise 拒绝:', e);
    console.log('原因:', e.reason);
});

var vm = new Vue({
    el: '#app',
    data: {
        // host:host,
        host,
        error_name: false,
        error_password: false,
        error_check_password: false,
        error_phone: false,
        error_allow: false,
        error_sms_code: false,
        sending_flag: false,

        username: '',
        password: '',
        password2: '',
        mobile: '',
        sms_code: '',
        allow: false,
        sms_code_tip: '获取短信验证码',  // a标签文字
        error_sms_code_message: '',  // 验证码错误提示信息
        error_name_message: '',
        error_phone_message: '',

    },
    methods: {
        // 检查用户名
        check_username: function () {
            var len = this.username.length;
            if (len < 5 || len > 20) {
                this.error_name_message = '请输入5-20个字符的用户名';
                this.error_name = true;
            } else {
                this.error_name = false;
            }
            /*
            // 检查重名
            if (this.error_name == false) {
                axios.get(this.host + '/usernames/' + this.username + '/count/', {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count > 0) {
                            this.error_name_message = '用户名已存在';
                            this.error_name = true;
                        } else {
                            this.error_name = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response.data);
                    })
            }
             */
        },
        check_pwd: function () {
            var len = this.password.length;
            if (len < 8 || len > 20) {
                this.error_password = true;
            } else {
                this.error_password = false;
            }
        },
        check_cpwd: function () {
            if (this.password != this.password2) {
                this.error_check_password = true;
            } else {
                this.error_check_password = false;
            }
        },
        // 检查手机号
        check_phone: function () {
            var re = /^1[3-9]\d{9}$/;
            if (re.test(this.mobile)) {
                this.error_phone = false;
            } else {
                this.error_phone_message = '您输入的手机号格式不正确';
                this.error_phone = true;
            }
            /*if (this.error_phone == false) {
                axios.get(this.host + '/mobiles/' + this.mobile + '/count/', {
                    responseType: 'json'
                })
                    .then(response => {
                        if (response.data.count > 0) {
                            this.error_phone_message = '手机号已存在';
                            this.error_phone = true;
                        } else {
                            this.error_phone = false;
                        }
                    })
                    .catch(error => {
                        console.log(error.response.data);
                    })
            }*/
        },
        check_sms_code: function () {
            if (!this.sms_code) {
                this.error_sms_code = true;
            } else {
                this.error_sms_code = false;
            }
        },
        check_allow: function () {
            if (!this.allow) {
                this.error_allow = true;
            } else {
                this.error_allow = false;
            }
        },

        // 发送短信验证码
        send_sms_code: function () {
            console.log('1. 开始执行');

            try {
                if (this.sending_flag == true) {
                    console.log('1.1 正在发送中，直接返回');
                    return;
                }
                this.sending_flag = true;
                console.log('2. 设置 sending_flag = true');

                // 校验参数，保证输入框有数据填写
                this.check_phone();
                console.log('3. 手机号验证完成, error_phone:', this.error_phone);

                if (this.error_phone == true) {
                    console.log('3.1 手机号验证失败，返回');
                    this.sending_flag = false;
                    return;
                }

                var requestUrl = this.host + '/sms_codes/' + this.mobile + '/';
                console.log('4. 准备发送请求到:', requestUrl);

                // 添加更详细的错误处理
                axios.get(requestUrl, {
                    responseType: 'json',
                    timeout: 10000 // 添加超时设置
                })
                    .then(response => {
                        console.log('5. 请求成功，响应数据:', response.data);
                        // 表示后端发送短信成功
                        var num = 60;
                        var t = setInterval(() => {
                            if (num == 1) {
                                clearInterval(t);
                                this.sms_code_tip = '获取短信验证码';
                                console.log('6. 倒计时结束');
                                this.sending_flag = false;
                            } else {
                                num -= 1;
                                this.sms_code_tip = num + '秒';
                            }
                        }, 1000)
                    })
                    .catch(error => {
                        console.log('=== 请求失败详情 ===');
                        console.log('错误完整对象:', error);
                        console.log('错误类型:', typeof error);
                        console.log('错误名称:', error.name);
                        console.log('错误消息:', error.message);

                        if (error.response) {
                            console.log('服务器响应错误:');
                            console.log('- 状态码:', error.response.status);
                            console.log('- 响应数据:', error.response.data);
                        } else if (error.request) {
                            console.log('网络请求错误:');
                            console.log('- 请求对象:', error.request);
                        } else {
                            console.log('其他错误:', error.message);
                        }

                        this.sending_flag = false;
                        console.log('设置 sending_flag = false');
                    })
            } catch (e) {
                console.log('=== 代码执行异常 ===');
                console.log('异常:', e);
                console.log('异常栈:', e.stack);
                this.sending_flag = false;
            }
        },
// 注册
        on_submit: function () {
            this.check_username();
            this.check_pwd();
            this.check_cpwd();
            this.check_phone();
            this.check_sms_code();
            this.check_allow();

            if (this.error_name == false && this.error_password == false && this.error_check_password == false
                && this.error_phone == false && this.error_sms_code == false && this.error_allow == false) {
                axios.post(this.host + '/users/', {
                    username: this.username,
                    password: this.password,
                    password2: this.password2,
                    mobile: this.mobile,
                    sms_code: this.sms_code,
                    allow: this.allow.toString()
                }, {
                    responseType: 'json'
                })
                    .then(response => {
                        // 记录用户的登录状态
                        sessionStorage.clear();
                        localStorage.clear();
                        localStorage.token = response.data.token;
                        localStorage.username = response.data.username;
                        localStorage.user_id = response.data.id;
                        location.href = '/index.html';

                    })
                    .catch(error => {
                        if (error.response.status == 400) {
                            if ('non_field_errors' in error.response.data) {
                                this.error_sms_code_message = error.response.data.non_field_errors[0];
                            } else {
                                this.error_sms_code_message = '数据有误';
                            }
                            this.error_sms_code = true;
                        } else {
                            console.log(error.response.data);
                        }
                    })
            }
        }
    }
});
