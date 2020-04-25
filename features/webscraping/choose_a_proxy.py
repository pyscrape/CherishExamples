# -*- coding:UTF-8 -*-
from bs4 import BeautifulSoup
from selenium import webdriver
import subprocess as sp
from lxml import etree
import requests
import random
import re

"""
http://www.xicidaili.com provides a list of :
All proxy IP addresses of this site are collected and compiled from the domestic public Internet. This site 
does not maintain and operate any proxy server. Please select by yourself.

Uses ping to get find a proxy which meets the latency tolerance.


Function description: Get IP proxy
Parameters:
	page - Hidden proxy pages, get the first page by default
Returns:
	proxys_list - Agent list
Modify:
	2017-05-27
"""
def get_proxys(page = 1):
	# requests Session can automatically keep cookies, no need to maintain cookie content yourself
	S = requests.Session()
	#Target IP Address
	target_url = 'http://www.xicidaili.com/nn/%d' % page
	#Perfect Headers
	target_headers = {'Upgrade-Insecure-Requests':'1',
		'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36',
		'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
		'Referer':'http://www.xicidaili.com/nn/',
		'Accept-Encoding':'gzip, deflate, sdch',
		'Accept-Language':'zh-CN,zh;q=0.8',
	}
	#Get request
	target_response = S.get(url = target_url, headers = target_headers)
	#utf-8 encoding
	target_response.encoding = 'utf-8'
	#Get web page information
	target_html = target_response.text
	#Get table with id ip_list
	bf1_ip_list = BeautifulSoup(target_html, 'lxml')
	bf2_ip_list = BeautifulSoup(str(bf1_ip_list.find_all(id = 'ip_list')), 'lxml')
	ip_list_info = bf2_ip_list.table.contents
	#List of storage agents
	proxys_list = []
	#Crawl each agent information
	for index in range(len(ip_list_info)):
		if index % 2 == 1 and index != 1:
			dom = etree.HTML(str(ip_list_info[index]))
			ip = dom.xpath('//td[2]')
			port = dom.xpath('//td[3]')
			protocol = dom.xpath('//td[6]')
			proxys_list.append(protocol[0].text.lower() + '#' + ip[0].text + '#' + port[0].text)
	#Back to agent list
	return proxys_list

"""
Function description: Check the connectivity of the proxy IP
Parameters:
	ip - Proxy ip address
	lose_time - Matching packet loss
	waste_time - Match average time
Returns:
	average_time - Proxy ip average time
Modify:
	2017-05-27
"""
def check_ip(ip, lose_time, waste_time):
	#Command -n Number of echo requests to send -w Timeout time to wait for each reply (ms)
	cmd = "ping -n 3 -w 3 %s"
	#Excecuting an order
	print(cmd)
	p = sp.Popen(cmd % ip, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, shell=True) 
	#Get return result and decode
	out = p.stdout.read().decode("gbk")
	print(out)
	# Number of packets lost
	lose_time = lose_time.findall(out)
	print(lose_time)
	#When matching the lost packet information fails, the default is to request all packets to be lost in
	# three times, and the number of lost packets is assigned a value of 3
	if len(lose_time) == 0:
		lose = 3
	else:
		lose = int(lose_time[0])

	# If the number of lost packets is greater than 2, the connection
	# is considered to time out and the average time to return is 1000ms
	if lose > 2:
		# Return False
		return 1000

	# If the number of lost packets is less than or equal to 2,
	# the average time taken to obtain
	else:
		# Average time
		average = waste_time.findall(out)

		# When the matching time-consuming information fails, the default three
		# times the request is severely timeout, and the average return is 1000ms
		if len(average) == 0:
			return 1000
		else:
			#
			average_time = int(average[0])
			#Return average time
			return average_time

"""
Function description: initialize regular expression
Parameters:
	无
Returns:
	lose_time - Matching packet loss
	waste_time - Match average time
Modify:
	2017-05-27
"""
def initpattern():
	# Match packet loss
	lose_time = re.compile(u"Lost = (\d+)", re.IGNORECASE)
	# Match average time
	waste_time = re.compile(u"average = (\d+)ms", re.IGNORECASE)
	#returns compiled regular expressions
	return lose_time, waste_time

if __name__ == '__main__':
	# Initialize regular expression
	lose_time, waste_time = initpattern()
	#Get IP proxy
	proxys_list = get_proxys(1)

	# If the average time exceeds 200ms, re-select ip
	while True:
		# Randomly select one IP from 100 IPs as a proxy to access
		proxy = random.choice(proxys_list)
		split_proxy = proxy.split('#')
		# Get IP
		ip = split_proxy[1]
		# Check ip
		average_time = check_ip(ip, lose_time, waste_time)
		if average_time > 200:
			# Remove unusable IP
			proxys_list.remove(proxy)
			print("ip connection timeout, Reacquiring!")
		if average_time < 200:
			break

	# Remove the used IP
	proxys_list.remove(proxy)
	proxy_dict = {split_proxy[0]:split_proxy[1] + ':' + split_proxy[2]}
	print("Use proxy:", proxy_dict)
