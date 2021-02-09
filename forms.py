from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, SubmitField, BooleanField, SelectField, TextAreaField, FloatField
from wtforms.validators import DataRequired, NumberRange

category_options = [
    ('電子產品類', '電子產品類'),
    ('手作類', '手作類'),
    ('工業類', '工業類'),
    ('運動用品類', '運動用品類'),
    ('戶外用品類', '戶外用品類'),
    ('玩具類', '玩具類'),
    ('保養品', '保養品'),
    ('其他', '其他')
]


class CreateProductForm(FlaskForm):
    # 建立商品的表單
    # 名稱(title)
    title = StringField('產品標題', validators=[DataRequired()])
    # 縮圖網址(img_url)
    img_url = StringField('產品圖片')
    # 價格(price)
    price = IntegerField('產品價格')
    # 是否銷售中(on_sale)
    on_sale = BooleanField('是否銷售中')
    # 類別(category)
    category = SelectField('類別', choices=category_options)
    # 敘述(description)
    description = TextAreaField('產品敘述')
    # 送出表單按鈕(submit)
    submit = SubmitField('建立商品')


class EditProductForm(FlaskForm):
    # 更新商品的表單
    # 名稱(title)
    title = StringField('產品標題', validators=[DataRequired()])
    # 縮圖網址(img_url)
    img_url = StringField('產品圖片')
    # 價格(price)
    price = IntegerField('產品價格')
    # 是否銷售中(on_sale)
    on_sale = BooleanField('是否銷售中')
    # 類別(category)
    category = SelectField('類別', choices=category_options)
    # 敘述(description)
    description = TextAreaField('產品敘述')
    # 送出表單按鈕(submit)
    submit = SubmitField('更新商品')


class DeleteProductForm(FlaskForm):
    # 移除商品的表單
    # 確認刪除
    confirm = BooleanField('確認是否移除?', validators=[DataRequired()])
    # 送出按鈕
    submit = SubmitField('移除商品')


class CreateCommentForm(FlaskForm):
    # 新增留言的表單
    email = StringField('Email', validators=[DataRequired()])
    content = TextAreaField('留言內容', validators=[DataRequired()])
    submit = SubmitField('發佈留言')


class UpdateCommentForm(FlaskForm):
    # 更新留言的表單
    content = TextAreaField('留言內容', validators=[DataRequired()])
    submit = SubmitField('更新留言')
