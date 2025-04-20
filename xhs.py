#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
小红书内容提取脚本
用于从小红书链接中提取标题、正文和配图
"""

import requests
from bs4 import BeautifulSoup
import re
import json
import os
import argparse
import sys
from urllib.parse import urlparse, parse_qs

def extract_xhs_content(url):
    """
    从小红书链接中提取标题、正文和配图
    
    Args:
        url (str): 小红书链接
        
    Returns:
        dict: 包含标题、正文和配图URL的字典
    """
    # 设置请求头，模拟浏览器访问
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }
    
    try:
        # 发送HTTP请求获取页面内容
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 如果请求失败，抛出异常
        
        # 使用BeautifulSoup解析HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 提取标题
        title = None
        og_title = soup.find('meta', attrs={'name': 'og:title'})
        if og_title:
            title = og_title.get('content', '')
        
        # 提取正文
        description = None
        og_description = soup.find('meta', attrs={'name': 'description'})
        if og_description:
            description = og_description.get('content', '')
        
        # 提取配图URL
        image_urls = []
        og_images = soup.find_all('meta', attrs={'name': 'og:image'})
        for img in og_images:
            img_url = img.get('content', '')
            if img_url:
                image_urls.append(img_url)
        
        # 提取互动数据
        likes = None
        comments = None
        collects = None
        
        # 尝试不同的方式获取互动数据
        og_like = soup.find('meta', attrs={'name': 'og:xhs:note_like'})
        if og_like:
            likes = og_like.get('content', '')
            
        og_comment = soup.find('meta', attrs={'name': 'og:xhs:note_comment'})
        if og_comment:
            comments = og_comment.get('content', '')
            
        og_collect = soup.find('meta', attrs={'name': 'og:xhs:note_collect'})
        if og_collect:
            collects = og_collect.get('content', '')
        
        # 返回提取的内容
        return {
            'title': title,
            'content': description,
            'image_urls': image_urls,
            'likes': likes,
            'comments': comments,
            'collects': collects
        }
    
    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None
    except Exception as e:
        print(f"提取内容时出错: {e}")
        return None

def download_images(image_urls, save_dir='images'):
    """
    下载图片到指定目录
    
    Args:
        image_urls (list): 图片URL列表
        save_dir (str): 保存图片的目录
        
    Returns:
        list: 下载的图片路径列表
    """
    # 创建保存目录
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    
    downloaded_paths = []
    
    for i, url in enumerate(image_urls):
        try:
            # 发送请求获取图片内容
            response = requests.get(url)
            response.raise_for_status()
            
            # 从Content-Type头中获取图片格式
            content_type = response.headers.get('Content-Type', '')
            if 'image/jpeg' in content_type:
                ext = '.jpg'
            elif 'image/png' in content_type:
                ext = '.png'
            elif 'image/webp' in content_type:
                ext = '.webp'
            else:
                # 默认使用.jpg
                ext = '.jpg'
            
            # 从URL中提取文件名，如果没有则使用索引
            parsed_url = urlparse(url)
            path_parts = parsed_url.path.split('/')
            filename = path_parts[-1] if path_parts else f"image_{i+1}{ext}"
            
            # 确保文件名有正确的扩展名
            if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                filename = f"{filename}{ext}"
            
            # 保存图片
            file_path = os.path.join(save_dir, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            downloaded_paths.append(file_path)
            print(f"已下载图片: {file_path}")
            
        except Exception as e:
            print(f"下载图片 {url} 时出错: {e}")
    
    return downloaded_paths

def main():
    # 创建命令行参数解析器
    parser = argparse.ArgumentParser(description='从小红书链接中提取内容')
    parser.add_argument('url', nargs='?', help='小红书链接')
    parser.add_argument('-o', '--output', default='images', help='图片保存目录 (默认: images)')
    parser.add_argument('-d', '--debug', action='store_true', help='显示调试信息')
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 如果没有提供URL，提示用户输入
    url = args.url
    if not url:
        url = input("请输入小红书链接: ")
    
    # 验证URL格式
    if not url.startswith('http'):
        url = 'https://' + url
    
    # 提取内容
    print(f"正在处理链接: {url}")
    content = extract_xhs_content(url)
    
    if content:
        print("\n=== 小红书内容 ===")
        print(f"标题: {content['title']}")
        print(f"\n正文:\n{content['content']}")
        print(f"\n图片数量: {len(content['image_urls'])}")
        
        if content['likes'] or content['comments'] or content['collects']:
            print(f"点赞数: {content['likes']}")
            print(f"评论数: {content['comments']}")
            print(f"收藏数: {content['collects']}")
        
        # 下载图片
        if content['image_urls']:
            print(f"\n正在下载图片到 {args.output} 目录...")
            downloaded_paths = download_images(content['image_urls'], args.output)
            print(f"已下载 {len(downloaded_paths)} 张图片")
        else:
            print("\n未找到图片")
    else:
        print("无法提取内容，请检查链接或网络连接")
        if args.debug:
            print("调试信息: 请确保链接格式正确，例如: https://www.xiaohongshu.com/explore/...")

if __name__ == "__main__":
    main()
