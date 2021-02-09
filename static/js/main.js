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
            console.log('[成功登入]', res)
            res.user.getIdToken()
                .then(idToken => {
                    console.log('[idToken]', idToken)
                })
        })
        // 如果登入失敗
        .catch(err => {
            console.log('[登入失敗]', err)
            const code = err.code;
            if (code == "auth/wrong-password") {
                alert('密碼錯誤')
            } else if (code == "auth/user-not-found") {
                alert('無此Email')
            } else if (code == "auth/too-many-requests") {
                alert('嘗試過多，請稍後再試')
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
});

$('#logoutBtn').click(function () {
    console.log('[登出]');
});