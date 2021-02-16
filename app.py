# 引用flask相關資源
# 引用各種表單類別
from forms import CreateCommentForm, CreateProductForm, DeleteCommentForm, DeleteProductForm, EditProductForm, UpdateCommentForm
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify, abort
import time
import firebase_admin
from firebase_admin import credentials, firestore, auth, exceptions
from flask_wtf import CSRFProtect
import datetime
import os

# db初始化
cred = credentials.Certificate(
    "./Firebase_adminkey.json")
firebase_admin.initialize_app(cred)
# 建立資料庫的實例(db)
db = firestore.client()


app = Flask(__name__)
csrf = CSRFProtect(app)
csrf.init_app(app)
# !設定應用程式的SECRET_KEY
app.config['SECRET_KEY'] = 'abc12345678'
# !設定快取時間為0
# app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
page_title = 'SH0PING'
cookie_name = 'flask_cookie'

# 轉換秒數時間為當地時間


def time_format(sec_time) -> str:
    localtime = time.localtime(sec_time)
    return str(localtime.tm_year) + '年' + \
        str(localtime.tm_mon) + '月' + str(localtime.tm_mday) + '日'


# 每個路由request之前都會先經過這關
@app.context_processor
def check_login():
    # 取得session_cookie
    session_cookie = request.cookies.get(cookie_name)
    # 預設登入狀態
    auth_state = {
        # 是否登入
        'is_login': False,
        # 是否為admin
        'is_admin': False,
        # 資料
        'user': {

        }
    }
    # 準備驗證
    try:
        # 用戶登入成功
        # 驗證session_cookie
        user_info = auth.verify_session_cookie(
            session_cookie, check_revoked=True)
        print('[用戶資料]', user_info)
        # 將資料存入登入狀態內
        auth_state['user'] = user_info
        # 取得user的email
        email = user_info['email']
        # 取得admin_list/{email} 文件
        admin_doc = db.document(f'admin_list/{email}').get()
        if admin_doc.exists:
            print(f'[{email}:是否為管理員]', admin_doc.exists)
            auth_state['is_admin'] = True
        # 將用戶標記為登入狀態
        auth_state['is_login'] = True
    except:
        # 用戶未登入
        print('[用戶未登入]')

    # 把auth_state發送至各個templates
    return dict(auth_state=auth_state)


# 路由保護邏輯
@app.before_request
def guard():
    auth_state = check_login()['auth_state']
    endpoint = request.endpoint
    is_admin = auth_state['is_admin']
    admin_route_list = [
        'create_product_page',
        'create_finished_page',
        'edit_product_page',
    ]
    # 如果使用者造訪管理員保護頁面，且非管理員
    if not is_admin and endpoint in admin_route_list:
        # 強制導向回首頁
        return redirect('/')


@app.route('/')
def index_page():
    # 取得資料庫的商品列表資料(product_list)
    # order_by為排序method,option arg有direction='DESCENDING' ->反向排序
    collection = db.collection('product_list').order_by(
        'created_at', direction='DESCENDING').get()
    # 建立產品列表
    product_list = []
    for doc in collection:
        product = doc.to_dict()
        product['created_at'] = time_format(product['created_at'])
        product['id'] = doc.id
        product_list.append(product)

    # 首頁路由
    return render_template('index.html', product_list=product_list, page_title=page_title)


@app.route('/api/login', methods=['POST'])
def login():
    print("準備開始登入API流程")
    # 取得前端傳給後端的資料
    id_token = request.json['idToken']
    # 設定session失效時間，7天
    expires_in = datetime.timedelta(days=7)
    try:
        # 產生 session cookie.
        session_cookie = auth.create_session_cookie(
            id_token, expires_in=expires_in)
        response = jsonify({'status': 'success'})
        # 將session_cookie寫入使用者瀏覽器內
        expires = datetime.datetime.now() + expires_in
        response.set_cookie(
            cookie_name, session_cookie, expires=expires, httponly=True)
        return response
    except exceptions.FirebaseError:
        return abort(401, 'idToken失效或Firebase掛了')


@app.route('/api/logout', methods=['POST'])
def logout():
    # 讓指定cookie失效
    respone = jsonify({'status': 'success'})
    respone.set_cookie(cookie_name, expires=0)
    return respone


@app.route('/product/create', methods=['GET', 'POST'])
def create_product_page():
    # 建立商品頁的路由
    page_title = '商品建立頁面'
    # 建立商品表單的實例
    form = CreateProductForm()
    # 設定表單送出後的處理
    if form.validate_on_submit():
        print('[新增商品表單被送出且沒有問題]')
        new_product = {
            'title': form.title.data,
            'img_url': form.img_url.data,
            'category': form.category.data,
            'price': form.price.data,
            'on_sale': form.on_sale.data,
            'description': form.description.data,
            'created_at': time.time()
        }
        print('[新增的商品]', new_product)
        # 把new_product存到資料庫內一個名為product_list的集合內
        db.collection('product_list').add(new_product)
        # 取得轉跳頁面的網址
        redirect_url = url_for('create_finished_page')
        print('[轉跳新頁面]', redirect_url)
        # 將新商品的資料儲存在session內以便下個頁面可顯示新資料
        # 把new_product存到session
        session['new_product'] = new_product
        # 回傳轉跳程序
        return redirect(redirect_url)
    return render_template('product/create.html', form=form, page_title=page_title)


@app.route('/product/create-finished')
def create_finished_page():
    page_title = '完成商品建立'
    # 從session取得new_product
    new_product = session['new_product']
    # 商品建立成功的路由
    return render_template('product/create_finished.html', new_product=new_product, page_title=page_title)


@app.route('/product/<pid>/show', methods=['GET', 'POST'])
def show_product_page(pid):
    # 商品詳情頁的路由
    # 取得資料庫指定pid的商品資料
    doc = db.collection('product_list').document(pid).get()
    product = doc.to_dict()
    product['created_at'] = time_format(product['created_at'])
    # 取得網頁標題
    page_title = product['title']+'｜介紹'
    # 建立留言表單
    created_comment_form = CreateCommentForm()
    # 如果表單被送出
    auth_state = check_login()['auth_state']
    if created_comment_form.validate_on_submit():
        email = auth_state['user']['email']
        new_comment = {
            'email': email,
            'content': created_comment_form.content.data,
            'created_at': time.time(),
        }
        print('新留言:', new_comment)
        # 把心留言存入product_list(集合)/pid(文件)/comment_list(集合)
        db.collection(f'product_list/{pid}/comment_list').add(new_comment)
        return redirect(f'/product/{pid}/show')
    # 取得該商品的留言
    comment_collection = db.collection(
        f'product_list/{pid}/comment_list').order_by('created_at', direction='DESCENDING').get()
    # 留言列表
    comment_list = []
    for doc in comment_collection:
        comment = doc.to_dict()
        comment['id'] = pid
        # 把更新留言的表單存到留言內
        # !在多表單的情況下加入prefix參數，可以幫每個表單加上不同前綴，以防伺服器混亂
        comment['update_form'] = UpdateCommentForm(prefix=doc.id)
        comment['del_form'] = DeleteCommentForm(prefix=doc.id+'-del')
        # 如果該表單被送出且合法
        if comment['update_form'].validate_on_submit():
            updated_comment = {
                'content': comment['update_form'].content.data
            }
            # 把資料更新到資料庫內
            db.document(
                f'product_list/{pid}/comment_list/{doc.id}').update(updated_comment)
            # 重新導向
            return redirect(f'/product/{pid}/show')

        if comment['del_form'].validate_on_submit():
            db.document(f'product_list/{pid}/comment_list/{doc.id}').delete()
            return redirect(f'/product/{pid}/show')

        # 把內容放入表單內當預設值
        comment['update_form'].content.data = comment['content']
        # 格式時間
        comment['created_at'] = time_format(comment['created_at'])
        comment_list.append(comment)

    return render_template('product/show.html',
                           product=product,
                           page_title=page_title,
                           created_comment_form=created_comment_form,
                           comment_list=comment_list)


@app.route('/product/<pid>/edit', methods=['GET', 'POST'])
def edit_product_page(pid):
    # 編輯商品頁的路由
    # 取得資料庫指定pid的商品資料
    doc = db.collection('product_list').document(pid).get()
    product = doc.to_dict()
    product['id'] = pid
    page_title = product['title']+'｜編輯頁'
    # 建立編輯商品表單的實例
    form = EditProductForm()
    # 建立刪除商品表單的實例
    form_del = DeleteProductForm()
    # 接收form回傳資料更新database
    if form.validate_on_submit():
        print('[更新商品表單被送出且沒有問題]')
        description = form.description.data.replace(u'\r\n', '&#010;')
        updated_product = {
            'title': form.title.data,
            'img_url': form.img_url.data,
            'price': form.price.data,
            'category': form.category.data,
            'on_sale': form.on_sale.data,
            'description': description
        }
        print('[更新的商品]', updated_product)
        # firebase更新document的method
        db.collection('product_list').document(pid).update(updated_product)
        # 轉跳回首頁
        return redirect('/')

    if form_del.validate_on_submit():
        # firebase刪除document的method
        db.collection('product_list').document(pid).delete()
        # 轉跳回首頁
        return redirect('/')

    # 把檢視商品的資料填入form內
    for field in form:
        if field != form['submit'] and field != form['csrf_token']:
            field.data = product[field.id]

    return render_template('product/edit.html', form=form, product=product, form_del=form_del, page_title=page_title)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    # !正式入口
    app.run(host='0.0.0.0', port=port)

    # !debug用
    # app.run(debug=True)
