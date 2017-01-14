# <API文档地址> http://aqicn.org/json-api/doc/#api-_
# API token: 87711e84f75008ae850fde4a59410486da3b8585
# http://api.waqi.info/feed/chengdu/?token=87711e84f75008ae850fde4a59410486da3b8585
# http://api.waqi.info/feed/here/?token=87711e84f75008ae850fde4a59410486da3b8585

import requests
from flask import Flask, render_template, redirect, url_for, flash, session, g
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard_to_guess_string'    # A secret key is required to use CSRF (flask-wtf)
app.config['DEBUG'] = True                           # 开启debug模式(自动reload)

manager = Manager(app)
bootstrap = Bootstrap(app)

aqi_request_url = 'http://api.waqi.info/feed/%s/?token=87711e84f75008ae850fde4a59410486da3b8585'


def get_aqi_level(aqi):
    """返回相应的空气质量等级"""
    if 0 <= aqi <= 50:
        return '好 (Good)'
    elif 51 <= aqi <= 100:
        return '中等 (Moderate)'
    elif 101 <= aqi <= 150:
        return '对敏感人群不健康 (Unhealthy for Sensitive Groups)'
    elif 151 <= aqi <= 200:
        return '不健康 (Unhealthy)'
    elif 201 <= aqi <= 300:
        return '非常不健康 (Very Unhealthy)'
    else:
        return '危险 (Hazardous)'


class QueryForm(FlaskForm):
    city_name = StringField('请输入城市名称 (英文小写字母, 如beijing, chongqing)',
                            validators=[DataRequired()])                        # [IMP] DataRequired后需有括号
    submit = SubmitField('提交')


@app.route('/', methods=['GET', 'POST'])
def index():
    form = QueryForm()
    if form.validate_on_submit():
        city_name = form.city_name.data
        try:
            res = requests.get(aqi_request_url % city_name, timeout=5).\
                json(encoding='utf-8')                                     # resp.json(encoding='utf-8')返回dict
            if res['status'] == 'error':
                flash('Request failed due to <%s>' % res['data'].upper())  # API请求失败,显示原因;重定向至首页
                return redirect(url_for('index'))                          # 简单web应用(没有蓝本)不需'.index'
            if res['status'] == 'ok':
                session['city_name'] = res['data']['city']['name']         # 将API请求的结果保存在session中
                session['query_aqi'] = res['data']['aqi']
                session['aqi_level'] = get_aqi_level(session.get('query_aqi'))
                session['query_time'] = res['data']['time']['s']
                session['show_query'] = True                 # [IMP] 设置session.show_query为True,用于判断重定向后的页面展示
                return redirect(url_for('index'))            # 重定向到主页,视图函数index()
        except requests.RequestException:
            flash('Request failed due to <%s>' % 'requests.RequestException')
            redirect(url_for('index'))

    if session.get('show_query'):                                      # [IMP] session.show_query为True; session中保存有数据
        # session['show_query'] = False: 用户对首页刷新后不再显示上次的查询结果(注释掉本行则会保留显示上次的查询结果)
        session['show_query'] = False
        return render_template('index.html',
                               form=form,
                               show_data_city=True,                    # show_data变量决定是否在模板中包含查询的数据
                               city_name=session.get('city_name'),
                               query_aqi=session.get('query_aqi'),
                               aqi_level=session.get('aqi_level'),
                               query_time=session.get('query_time'))
    else:
        return render_template('index.html',
                               form=form,
                               show_data_city=False)                   # show_data变量决定是否在模板中包含查询的数据


if __name__ == '__main__':
    app.run(port=5000)

