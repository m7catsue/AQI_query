# <API文档地址> http://aqicn.org/json-api/doc/#api-_
# API token: 87711e84f75008ae850fde4a59410486da3b8585
# http://api.waqi.info/feed/chengdu/?token=87711e84f75008ae850fde4a59410486da3b8585
# http://api.waqi.info/feed/here/?token=87711e84f75008ae850fde4a59410486da3b8585

# Multiple forms in a single page using flask and WTForms
# http://stackoverflow.com/questions/18290142/multiple-forms-in-a-single-page-using-flask-and-wtforms

import requests
from decimal import Decimal
from flask import Flask, render_template, redirect, url_for, flash, session, request
from flask_script import Manager
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SubmitField, ValidationError
from wtforms.validators import DataRequired, NumberRange

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hard_to_guess_string'    # A secret key is required to use CSRF (flask-wtf)
app.config['DEBUG'] = True                           # 开启debug模式(自动reload)

manager = Manager(app)
bootstrap = Bootstrap(app)

request_url = 'http://api.waqi.info/feed/%s/?token=87711e84f75008ae850fde4a59410486da3b8585'


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
    """通过过城市名称查询的表单"""
    city_name = StringField('输入城市名称 (英文小写字母, 如beijing, chongqing)',
                            validators=[DataRequired()])                        # [IMP] DataRequired后需有括号
    submit = SubmitField('提交城市查询')


class SubmitIP(FlaskForm):
    """提交当前IP地址的表单"""
    submit = SubmitField('查询当前IP地址')


class GeoForm(FlaskForm):
    """提交经纬度的表单"""
    latitude = DecimalField('输入纬度', places=3, validators=[DataRequired(), NumberRange(-90, 90)])
    longitude = DecimalField('输入经度', places=3, validators=[DataRequired(), NumberRange(-180, 180)], )
    submit = SubmitField('提交经纬度查询')


@app.route('/', methods=['GET', 'POST'])
def index():
    # [IMP] adds a prefix to a form and then check for the prefix with validate_on_submit()
    # [IMP] 增加prefix为防止以外触发同一页面的其他form的submit button
    query_city_form = QueryForm(prefix='query_city_form')            # 通过城市名称查询的表单
    query_ip_form = SubmitIP(prefix='query_ip_form')                 # 通过IP地址查询的表单
    query_geo_form = GeoForm(prefix='query_geo_form')                # 通过过经纬度查询的表单

    # (1)提交根据城市名称进行AQI查询
    # [IMP] 若submit则submit.data的值为True;额外增加这层对submit.data的验证是为了防止意外触发同一页面的其他form的submit button
    if query_city_form.submit.data and query_city_form.validate_on_submit():
        city_name = query_city_form.city_name.data
        try:                                                                     # resp.json(encoding='utf-8')返回dict
            res = requests.get(request_url % city_name, timeout=5).json(encoding='utf-8')
            if res['status'] == 'error':
                flash('Request failed due to <%s>' % res['data'].upper())        # API请求失败,显示原因;重定向至首页
                return redirect(url_for('index'))                                # 简单web应用(没有蓝本)不需'.index'
            if res['status'] == 'ok':
                session['city_name'] = res['data']['city']['name']               # 将API请求的结果保存在session中
                session['query_aqi'] = res['data']['aqi']
                session['aqi_level'] = get_aqi_level(session.get('query_aqi'))
                session['query_time'] = res['data']['time']['s']
                session['show_city_query'] = True
                session['show_ip_query'] = False
                session['show_geo_query'] = False
                return redirect(url_for('index'))  # 设置session.show_xx_query为True, 用于判断重定向后的页面展示
        except requests.RequestException:
            flash('Request failed due to <%s>' % 'requests.RequestException')
            redirect(url_for('index'))

    # (2)提交根据经纬度进行AQI查询
    if query_geo_form.submit.data and query_geo_form.validate_on_submit():
        lon = query_geo_form.longitude.data
        lat = query_geo_form.latitude.data
        argument_geo = 'geo:%s;%s' % (lat, lon)
        try:
            print(request_url % argument_geo)
            res = requests.get(request_url % argument_geo, timeout=5).json(encoding='utf-8')
            if res['status'] == 'error':
                flash('Request failed due to <%s>' % res['data'].upper())
            if res['status'] == 'ok':
                session['city_name'] = res['data']['city']['name']
                session['query_aqi'] = res['data']['aqi']
                session['aqi_level'] = get_aqi_level(session.get('query_aqi'))
                session['query_time'] = res['data']['time']['s']
                session['show_city_query'] = False
                session['show_geo_query'] = True
                session['show_ip_query'] = False
                return redirect(url_for('index'))  # 设置session.show_xx_query为True, 用于判断重定向后的页面展示
        except requests.RequestException:
            flash('Request failed due to <%s>' % 'requests.RequestException')

    # (3)提交根据用户IP地址进行AQI查询
    if query_ip_form.submit.data and query_ip_form.validate_on_submit():
        visitor_ip = request.remote_addr
        try:
            res = requests.get(request_url % 'here', timeout=5).json(encoding='utf-8')
            if res['status'] == 'error':
                flash('Request failed due to <%s>' % res['data'].upper())
            if res['status'] == 'ok':
                session['city_name'] = res['data']['city']['name']
                session['query_aqi'] = res['data']['aqi']
                session['aqi_level'] = get_aqi_level(session.get('query_aqi'))
                session['query_time'] = res['data']['time']['s']
                session['visitor_ip'] = visitor_ip                         # 保存访客ip
                session['show_city_query'] = False
                session['show_geo_query'] = False
                session['show_ip_query'] = True
                return redirect(url_for('index'))  # 设置session.show_xx_query为True, 用于判断重定向后的页面展示
        except requests.RequestException:
            flash('Request failed due to <%s>' % 'requests.RequestException')
            return redirect(url_for('index'))

    # 重定性回首页显示查询结果
    # session.show_xx_query为True;session中保存有数据
    # session['show_query'] = False: 用户对首页刷新后不再显示上次的查询结果(注释掉本行则会保留显示上次的查询结果)
    if session.get('show_city_query'):
        session['show_city_query'] = False
        return render_template('index.html',
                               query_city_form=query_city_form,
                               query_ip_form=query_ip_form,
                               query_geo_form=query_geo_form,
                               show_city_data=True,                        # show_xx_data变量决定是否在模板中包含查询的数据
                               show_ip_data=False,
                               show_geo_data=False,
                               city_name=session.get('city_name'),
                               query_aqi=session.get('query_aqi'),
                               aqi_level=session.get('aqi_level'),
                               query_time=session.get('query_time'))
    if session.get('show_ip_query'):
        session['show_ip_query'] = False
        return render_template('index.html',
                               query_city_form=query_city_form,
                               query_ip_form=query_ip_form,
                               query_geo_form=query_geo_form,
                               show_city_data=False,
                               show_ip_data=True,
                               show_geo_data=False,
                               visitor_ip=session.get('visitor_ip'),
                               city_name=session.get('city_name'),
                               query_aqi=session.get('query_aqi'),
                               aqi_level=session.get('aqi_level'),
                               query_time=session.get('query_time'))
    if session.get('show_geo_query'):
        session['show_geo_query'] = False
        return render_template('index.html',
                               query_city_form=query_city_form,
                               query_ip_form=query_ip_form,
                               query_geo_form=query_geo_form,
                               show_city_data=False,
                               show_ip_data=False,
                               show_geo_data=True,
                               city_name=session.get('city_name'),
                               query_aqi=session.get('query_aqi'),
                               aqi_level=session.get('aqi_level'),
                               query_time=session.get('query_time'))
    else:
        return render_template('index.html',
                               query_city_form=query_city_form,
                               query_ip_form=query_ip_form,
                               query_geo_form=query_geo_form,
                               show_city_data=False,
                               show_ip_data=False,
                               show_geo_data=False)


if __name__ == '__main__':
    app.run(port=5000)

