# 引用flask相關資源
# 引用各種表單類別
from forms import CreateCommentForm, CreateProductForm, DeleteProductForm, EditProductForm, UpdateCommentForm
from flask import Flask, render_template, request, session, redirect, url_for, flash, jsonify
import time
import firebase_admin
from firebase_admin import credentials, firestore

# db初始化
cred = credentials.Certificate(
    "./Firebase_adminkey.json")
firebase_admin.initialize_app(cred)
# 建立資料庫的實例(db)
db = firestore.client()


app = Flask(__name__)

# !設定應用程式的SECRET_KEY
app.config['SECRET_KEY'] = 'abc12345678'
# !debug用 cache為零
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
page_title = '主頁'


# 轉換秒數時間為當地時間
def time_format(sec_time) -> str:
    localtime = time.localtime(sec_time)
    return str(localtime.tm_year) + '年' + \
        str(localtime.tm_mon) + '月' + str(localtime.tm_mday) + '日'


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
    if created_comment_form.validate_on_submit():
        new_comment = {
            'email': created_comment_form.email.data,
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
        comment['form'] = UpdateCommentForm(prefix=doc.id)
        # 如果該表單被送出且合法
        if comment['form'].validate_on_submit():
            updated_comment = {
                'content': comment['form'].content.data
            }
            # 把資料更新到資料庫內
            db.document(
                f'product_list/{pid}/comment_list/{doc.id}').update(updated_comment)
            # 重新導向
            return redirect(f'/product/{pid}/show')

        # 把內容放入表單內當預設值
        comment['form'].content.data = comment['content']
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


if __name__ == '__main__':
    # 應用程式開始運行
    app.run(debug=True)
