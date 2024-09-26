import requests
from bs4 import BeautifulSoup

MAX_SUMMARY_LEN = 200

GSTONEGAMES_DOMAIN = "https://www.gstonegames.com"


# 发送请求获取网页内容
def getGoodsList():
    items = []
    keyword = "炸弹猫"
    url = GSTONEGAMES_DOMAIN + "/game/?keyword=" + keyword
    response = requests.get(url)
    html_content = response.text
    # 使用 BeautifulSoup 解析网页内容
    soup = BeautifulSoup(html_content, 'html.parser')
    # 查找 class 为 goods-list 的元素
    goods_list = soup.find_all(class_='goods-list fl')
    # 如果找到了 goods-list 元素，则输出其中的标签信息
    if goods_list:
        # 提取商品信息
        for goods in goods_list:
            print(goods.prettify())
            publication_year = "未知"
            game_mode = "未知"
            game_category = "未知"
            player_number = "未知"
            average_game_time = "未知"
            difficulty_level = "未知"
            game_ame = goods.find('div', class_='goods-title').find('a').text  # 游戏名称
            href_link = GSTONEGAMES_DOMAIN + goods.find('div', class_='goods-title').find('a')['href']  # 游戏链接
            img_link = goods.find('div', class_='goods-img').find('img')['src'].replace("//", "", 1)  # 游戏图片
            tags = goods.find('div', class_='goods01').text.split('\xa0/\xa0')
            if len(tags) >= 3:
                publication_year = tags[0]  # 出版年份
                game_mode = tags[1]  # 游戏模式
                game_category = tags[2]  # 游戏分类
            # 提取人数等信息
            people_info_list = goods.find('div', class_='goods02').findAll('span')
            if len(people_info_list) >= 3:
                player_number = people_info_list[0].text  # 玩家人数
                average_game_time = people_info_list[1].text  # 人均时长
                difficulty_level = people_info_list[2].text  # 难度等级
            score = goods.find('div', class_='goods04').find('span').text  # 游戏评分
            items.append({
                "game_ame": game_ame,
                # "short_summary": summary[:MAX_SUMMARY_LEN] + '...',
                "href_link": href_link,
                "img_link": img_link,
                "publication_year": publication_year,
                "game_mode": game_mode,
                "game_category": game_category,
                "player_number": player_number,
                "average_game_time": average_game_time,
                "difficulty_level": difficulty_level,
                "score": score
            })
    else:
        print("没有找到商品信息")
    print(items)
    return items
