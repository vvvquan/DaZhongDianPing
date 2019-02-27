#!/usr/bin/env python
# -*- coding:utf-8 -*-

from bs4 import BeautifulSoup #抓取html源码中的标签
from urllib import request  #发起请求
import xlrd   #读excel
import xlwt   #写excel
import re     #正则表达式
import random #随机数
import time
import sys

#==========================================
# 获取HTML源码
##=========================================
def getHtml(url):
	data = None
	headers = {
		'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36',
		'Referer':'http://www.dianping.com/guangzhou/ch10'
	}
	req = request.Request(url=url, headers=headers)
	html = request.urlopen(req).read().decode('utf-8', 'ignore')
	return html

#==========================================
##把商家信息保存到excel表格中
#==========================================
def saveBusiness(wb, items, num):
	ws = wb.add_sheet('sheet'+str(num))
	headData = ['商户名','口味评分','环境评分','服务评分','人均价格','评论数量','星级','好评数','差评数','前10条中的优质评论数']
	headDataLen = len(headData)
	for column in range(0,headDataLen):
		ws.write(0, column, headData[column], xlwt.easyxf('font: bold on'))
	index = 1
	lens = len(items)
	for j in range(0, lens):
		for i in range(0, headDataLen):
			ws.write(index, i, items[j][i])
		index += 1
	wb.save('DZDP.xls')

#========================================
##把键值对与数字对应生成字典
#========================================
def number():
    changedic = {}
    changedic['<d class="iov09"></d>'] = '0'
    changedic['<d class="iou67"></d>'] = '2'
    changedic['<d class="iorlu"></d>'] = '3'
    changedic['<d class="ioi08"></d>'] = '4'
    changedic['<d class="iolur"></d>'] = '5'
    changedic['<d class="io1u0"></d>'] = '6'
    changedic['<d class="iokqf"></d>'] = '7'
    changedic['<d class="iotpa"></d>'] = '8'
    changedic['<d class="ioke6"></d>'] = '9'
    return changedic
#========================================
#把键值对替换为对应的字符
##========================================
def change(dic,text):
    for key,value in dic.items():
        text = text.replace(key, value)
    return text
#========================================
#获得大众点评数字相关内容的函数
#========================================
def score(changedic, soup):
    inf = {}
    inf['tel'] = re.findall(r'</span> (.*?) </p>',change(changedic,str(soup.find('p',class_='expand-info tel'))))[0]
    inf['review'] = re.findall(r'> (.*?) 条评论',change(changedic,str(soup.find('span',id='reviewCount'))))[0]
    #人均这一项有的是人均：20元/有的是人均：-
    #加一个try/except把两种都考虑进去
    item = soup.find('span',id='avgPriceTitle')
    try:
        inf[re.findall(r'>(.*?) 元',change(changedic,str(item)))[0].split(':')[0]] = re.findall(r'>(.*?) 元',change(changedic,str(item)))[0].split(':')[1].strip()
    except:
        inf[item.text.split(':')[0]] = ''
    #一些网页并没有环境，口味等等这种评分，没有就跳过
    try:
        soup = soup.find('span', id='comment_score').find_all('span', class_='item')
        for i in soup:
            k = re.findall(r'<span class="item">(.*?) </span>', change(changedic, str(i)))[0]
            inf[k.split(':')[0]] = k.split(':')[1].strip()
    except Exception:
        pass
    return inf

#==========================================
##获取广州市的行政区的所有url
##==========================================
def get_region_url(url):
	html = getHtml(url)
	soup = BeautifulSoup(html, 'lxml')
	soup_list = soup.find('div', {'id':'region-nav'}).find_all('a')
	url_list = [i['href'] for i in soup_list]
	return url_list
#==========================================
##获取url的页面中所有商家的链接
##==========================================
def get_shop_url(url):
	html = getHtml(url)
	soup = BeautifulSoup(html, 'lxml')
	shop_list = soup.find_all('div', {'class':'tit'})
	return [i.find('a')['href'] for i in shop_list]

#===========================================
# 获取url的页面中的详细信息
##==========================================
def get_details_content(numdic, url):
	html = getHtml(url)
	soup = BeautifulSoup(html, 'lxml')

	price = soup.find('span', {'id':'avgPriceTitle'}) #人均价格
	price = change(numdic, str(price))
	#人均这一项有的是人均：20元/有的是人均：-
	#加一个try/except把两种都考虑进去
	try:
		price = re.findall(r': (.*?) 元', price)[0]
	except:
		price = '-'

	try:
		evaluation = soup.find('span', {'id':'comment_score'}).find_all('span', class_='item')  #3个评价得分
		evaluation = change(numdic, str(evaluation))
		score = evaluation.split(',')
		score[0] = re.findall(r': (.*?) </span>', score[0])[0]
		score[1] = re.findall(r': (.*?) </span>', score[1])[0]
		score[2] = re.findall(r': (.*?) </span>', score[2])[0]
	except Exception as e:
		print("score error: " + str(e))
	
	try:
		the_star = (soup.find('div', {'class':'brief-info'}).find('span'))['class'] #星级评定
		star = str(the_star[1])
		star = star[7]+'.'+star[8]
	except Exception as e:
		star = "0"
		print("star error: " + str(e))

	title = soup.find('div', {'class':'breadcrumb'}).find('span').text  #店名

	try:
		comments = soup.find('span', {'id':'reviewCount'})  #评论数量
		comments = change(numdic, str(comments))
		comments = re.findall(r'> (.*?) 条评论', comments)[0]
	except Exception as e:
		comments = "0"
		print("comments error: " + str(e))

	try:
		good = soup.find('label', {'class':'filter-item J-filter-good'}).text  #好评数
		good = re.findall(r'\((.*?)\)', str(good))[0]
	except Exception as e:
		good = "0"
		print("good error: " + str(e))

	try:
		bad = soup.find('label', {'class':'filter-item J-filter-bad'}).text  #差评数
		bad = re.findall(r'\((.*?)\)', str(bad))[0]
	except Exception as e:
		bad = "0"
		print("bad error: " + str(e))

	good_comment = 0 #优质评论数
	try:
		reviews = soup.find_all('div',{'class':'content'})  #所有评论和图片
		for review in reviews:
			word = review.find('p',{'class':'desc J-desc'}) #评论内容
			wordcnt = count_word(str(word)) #统计评论字数
			img = review.find('div', {'class':'photos'}).find_all('a')
			imgcnt = len(img) #配图数目
			if (wordcnt >= 150 and imgcnt >= 3):
				good_comment += 1
	except Exception as e:
		print("good_comment error: " + str(e))
	good_comment = str(good_comment)

	print('店名：'+title)
	print('口味：'+score[0])
	print('环境：'+score[1])
	print('服务：'+score[2])
	print('人均价格：'+price)
	print('评论数：'+comments)
	print('星级：' +star)
	print('好评数：'+good)
	print('差评数：'+bad)
	print('优质评论数：'+good_comment)
	print('============================')
	return (title, score[0], score[1], score[2], price, comments, star, good, bad, good_comment)

#========================================
# 获取每个评论的情感词语个数和配图个数
# 从而计算出每个商家的优质评论个数
#========================================
def count_word(item):
	s2 = re.sub(r'<.*?>','', item)
	# s2中可能含有'\n'，要去掉
	s2 = s2.replace('\n','')
	return len(s2)

#========================================
# 主程序
#========================================
if __name__ == '__main__':
	# 爬虫开始
	base_url = 'http://www.dianping.com/guangzhou/ch10/r1519o2'  #美食 天河 按人气排序
	region_url_list = get_region_url(base_url)
	region_url_list = [base_url]

	wb = xlwt.Workbook('DZDP.xls')

	numdic = number() #numdic是数字对应的字典
	for url in region_url_list:
		for i in range(47,51):   #第1到50页#################################################
			shop_url_list = get_shop_url(base_url+'p'+str(i))
			items = []
			for details_url in shop_url_list:
				print(details_url)
				time.sleep(random.uniform(3,5))
				try:
					item = get_details_content(numdic, details_url)
					items.append(item)
				except Exception as e:
					print("error"+str(e))
			saveBusiness(wb, items, i)