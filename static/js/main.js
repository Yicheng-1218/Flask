function finalizeLogin(res) {
    res.user.getIdToken()
        .then(idToken => {
            // console.log('[idToken]', idToken)
            // 把idToken送到後端api
            axios.post('/api/login', { idToken }, axiosConfig)
                .then(res => {
                    console.log('[完成idToken後端回應]', res);
                    // 重整畫面
                    window.location.reload();
                })
                .catch(err => {
                    console.log('[傳遞idToken失敗]', err);
                    alert(err.message)
                })
        })
}

$('#loginForm').submit(function (event) {
    // 防止頁面重整
    event.preventDefault();
    const form = {
        email: $('#loginEmail').val(),
        password: $('#loginPassword').val(),
    };
    console.log('[登入]', form);
    firebase
        .auth()
        .signInWithEmailAndPassword(form.email, form.password)
        // 如果登入成功
        .then(res => {
            console.log('[成功登入]', res);
            finalizeLogin(res);
        })
        // 如果登入失敗
        .catch(err => {
            console.log('[登入失敗]', err)
            const code = err.code;
            if (code == "auth/wrong-password") {
                alert('密碼錯誤');
            } else if (code == "auth/user-not-found") {
                alert('無此Email');
            } else if (code == "auth/too-many-requests") {
                alert('嘗試過多，請稍後再試');
            } else if (code == 'auth/user-disabled') {
                alert('您的帳戶已被管理員停用')
            }

        });
});

$('#signUpForm').submit(function (event) {
    event.preventDefault();
    const form = {
        email: $('#signUpEmail').val(),
        password: $('#signUpPassword').val(),
    };
    console.log('[註冊]', form);
    firebase.auth()
        .createUserWithEmailAndPassword(form.email, form.password)
        .then(res => {
            console.log('註冊成功', res);
            finalizeLogin(res);
        })
        .catch(err => {
            console.log('[err]', err);
            const code = err.code;
            if (code == 'auth/email-already-in-use') {
                alert('此Email已被註冊');
            } else if (code == 'auth/invalid-email') {
                alert('Email格式不正確');
            } else if (code == "auth/too-many-requests") {
                alert('嘗試過多，請稍後再試');
            }
        })
});

$('#logoutBtn').click(function () {
    console.log('[登出]');
    axios.post('/api/logout', {}, axiosConfig)
        .then(res => {
            // 引導回首頁
            window.location = '/';
        })
        .catch(err => {
            console.log('[err]', err);
            alert(err);
        })
});

