import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin, urlparse
import csv
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from pyautogui import hotkey

headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8"
        }

def get_config():
    jjs = ''
    with open('sm.json') as file:
        jjs = json.load(file)
    return jjs


def genrateFile(url,flag):
   parsed_url = urlparse(url)
   domin = 'https://' + parsed_url.netloc
   site_name = parsed_url.netloc.split('.')[-2]
   path  =''
   filename = path+site_name+'data.csv'

   # step 2
   jjs = get_config()

   if flag == '1':
    return domin,site_name
   elif flag == '2':
    return domin,site_name,filename



# دالة تستكشف جميع المقالات بالصفحة وترجع روابطها 

def get_page_links(url,classes,excluded_Grob):

  domin,site_name  = genrateFile(url,'1')




  print('geting artacls... \n')
  session = requests.Session()
  response = session.get(url, headers=headers)
  lll = []





  if response.status_code == 200:
    html = response.text
    soup = BeautifulSoup(html, 'html.parser')

    if classes['aClass'] is not None:
      a_tags = soup.find_all('a',class_=classes['aClass'])
      for a_tag in a_tags:
        href = a_tag.get('href')
        if href is not None:
          if not href.startswith('http'):
            href = urljoin(domin, href)
          if href not in lll:
            lll.append(href)
    else:
      tops = soup.find_all(class_=classes['alltopec'])
      for top in tops:
        a_tags = top.find_all('a')
        for a_tag in a_tags:
          href = a_tag.get('href')
          if href is not None:
            if not href.startswith('http'):
              href = urljoin(domin, href)
            if href not in lll:
              lll.append(href)



# التخلص من الروابط الغير مرغوب فيها حسب الكلمات المعرفة مسبقا
  links = []
  for href in lll:
    contains_target_word = False
    for word in excluded_Grob['excluded_url_words']:
      if word in href:
        contains_target_word = True
        break
    if not contains_target_word:
      links.append(href)




  topc_total = len(links)
  print(f'found  {topc_total} articals')
  return links


# دالة تبداء العمل بحيث تستقبل الرابط والكلاسات والكلمات المستبعده وتبداء بتشغيل الدوال للاستخراج
def goToWork(url,clasess,excluded_Grob):
  links = get_page_links(url,clasess,excluded_Grob)
  scrape_content(links,url,clasess,excluded_Grob)




# دالة خاصة بخاصية فتح الموقع وجلب الكلاس بشكل تلقائي
def get_page_linkTow(url,map_of_classes,excluded_Grob):
    
    clasess={'alltopec':None,'aClass':None,'info':None,'content':None}
    if map_of_classes['aClass']!='':
        clasess['aClass'] = map_of_classes['aClass']
        goToWork(url=url,clasess=clasess,excluded_Grob=excluded_Grob)
         
    elif map_of_classes['parantClass']!='':
        clasess['alltopec'] = map_of_classes['parantClass']
        goToWork(url=url,clasess=clasess,excluded_Grob=excluded_Grob)
         
        
    


# دالة تستقبل صفحة المقالة وتستخرج منها تفاصيل المقالة وترجعه
def writ (soup,url,classes,excluded_Grob):
  written_titles = set()
  written_content = set()
  written_info = set()


  domin,site_name  = genrateFile(url,'1')
  count = 0



  allContetn = {'tital':'','info':'','content':''}



  h1_element = soup.find_all('h1')
  titlaText = ''
  for ee in h1_element:
    if ee is not None:
      if ee.text.strip() not in excluded_Grob['excluded_content_words'] and ee.text.strip() not in written_titles:
        written_titles.add(titlaText)

        titlaText = titlaText + ee.text

  allContetn['tital'] = titlaText

  article_author=""
  if classes['info'] is not None:
    article_author = soup.find(class_=classes['info'])
    author_text = ''
    if article_author.text:
      author_text = article_author.text+'\n'
    text_elements = [element.text for element in article_author.find_all(text=True) if element.text.strip()]
    for te in text_elements:
      if te.strip() not in written_info:
        author_text+=te+'\n'
        written_info.add(te)

    allContetn['info']= author_text



  textContent = ''

  if classes['content'] is not None:

    content = soup.find(class_=classes['content'])
    content_items = content.find_all()
    for item in content_items:

      if any(cls in excluded_Grob['excluded_content_classes'] for cls in item.get('class', [])):
        item.extract()


    tt_elements = [element.text for element in content.find_all(text=True) if element.text.strip()]
    for tt in tt_elements:
      if tt.strip() not in written_content:
        textContent+=tt+'\n'
        written_content.add(tt)
    allContetn['content']=textContent
  else:
    prag = soup.find_all('p')
    for p in prag:
      if p is not None and p.text.strip() not in written_content:
        textContent= textContent+ p.text+'\n'
        written_content.add(p.text)
        allContetn['content']=textContent



  return allContetn

# دالة تطلب صفحات المقالات وبعد جلب المحتوى تقوم بكتابته على الملف
def scrape_content(links,url,classes,excluded_Grob):
  count = 0

  fieldnames = ['العنوان', 'المحتوى','معلومات']
  domin,site_name , filename = genrateFile(url,'2')

  total = len(links)


  print('having artacls.... \n')
  with open(filename, 'w', encoding='utf-8-sig', newline='') as file:
    writer = csv.DictWriter(file, fieldnames=fieldnames)
    writer.writeheader()
    for link in links:
      response2 = requests.get(link, headers=headers)
      if response2.status_code == 200:
        html2 = response2.text
        soup2 = BeautifulSoup(html2, 'html.parser')

        allContetn =writ(soup=soup2,url=url,classes=classes,excluded_Grob=excluded_Grob)

        writer.writerow({'العنوان': allContetn['tital'], 'المحتوى': allContetn['content'],'معلومات':allContetn['info']})
        count+=1
        print(f'done {count} from {total} ')

        if count == 20:
          break

  print('done all')










# دالة تفتح الموقع وتمكن المستخدم من تحديد الديف بالماوس وبيتم اخذ الكلاس بشكل تلقائي
def openWebSite(url):
  driver = webdriver.Chrome()
  driver.get(url)
  while True:
    
    hotkey('ctrl')

    
    hovered_element = driver.execute_script("""
    var clickedElement = null;
    document.addEventListener('contextmenu', function(event) {
        event.preventDefault();
        clickedElement = event.target;
    });

    var target = document.elementFromPoint(window.innerWidth / 2, window.innerHeight / 2);
    while (target.parentElement) {
        var validTags = ['div', 'h2', 'p'];
        if (validTags.includes(target.tagName.toLowerCase()) && target.querySelector('a')) {
            target.dispatchEvent(new Event('contextmenu', {
                bubbles: true,
                cancelable: true,
                composed: true
            }));
            break;
        }
     
        target = target.parentElement;
    }

    return clickedElement;
""")




    map_of_classes = {'parantClass':None,'aClass':None,'simpleUrl':None}
    # Check if element found
    if hovered_element:
        p_tage = hovered_element.tag_name
        p_clas = hovered_element.get_attribute("class")
        
        if p_tage == 'div' or p_tage == 'h2' or p_tage == 'p':
            a_tag = hovered_element.find_element(by=By.TAG_NAME,value='a')
            a_calss = a_tag.get_attribute("class")
            href = a_tag.get_attribute("href")
            map_of_classes['parantClass'] = p_clas
            map_of_classes['aClass'] = a_calss
            map_of_classes['simpleUrl'] = href
            
    # else:
    #     a_tag = hovered_element
    #     a_calss = a_tag.get_attribute("class")
    #     href = a_tag.get_attribute("href")
           
        

        
        
        
        
            
        break  
  
  return map_of_classes




#دالة تختبر اذا كان الموقع موجود 
# اذا لم يكن موجود :
# مطلوب كلاسات الاساسية

def ChickUrlTarget(url,u_word,c_class,c_word,alltopecClass=None,aClass=None,contentClass=None,infoClass=None):
  jsonFile = get_config()
  classes = {'alltopec':None,'aClass':None,'info':None,'content':None}
  excluded_Grob = {'excluded_url_words':u_word,'excluded_content_classes':c_class,'excluded_content_words':c_word}

  domin,site_name = genrateFile(url,'1')
  if site_name not in jsonFile['pClass'] and site_name not in jsonFile['alltopec'] :

    if alltopecClass is None and aClass is None:
      
      map_of_classes  = openWebSite(url=url)
    #   print(map_of_classes)
      get_page_linkTow(url=url,map_of_classes=map_of_classes,excluded_Grob=excluded_Grob)

    elif alltopecClass is not None or aClass is not None:
      
      classes['alltopec'] = alltopecClass
      classes['aClass'] = aClass

      if contentClass is None and infoClass is None:
        pass

      elif contentClass is not None or infoClass is not None:
         
         classes['info'] = infoClass
         classes['content'] = contentClass

      goToWork(url,classes,excluded_Grob)

  elif site_name in jsonFile['pClass'] or site_name in jsonFile['alltopec'] :
    
    if site_name in jsonFile['info']:
      classes['info'] =  jsonFile['info'][site_name]
    if site_name in jsonFile['content']:
      classes['content'] =  jsonFile['content'][site_name]
    if site_name in jsonFile['pClass']:
      classes['aClass'] = jsonFile['pClass'][site_name]
    else:
      classes['alltopec'] = jsonFile['alltopec'][site_name]

    goToWork(url,classes,excluded_Grob)




web_url = 'https://www.aljazeera.net/sports/'
# web_url = ' https://www.al-monitor.com/technology'
# https://www.al-monitor.com/technology


alltopecClass = None
aClass= None
# مطلوب احدهما اذا كان الموقع ليس ضمن القائمة
 #  الكلاس الاب لصفحة جميع المقالات
#  الكلاس الخاص بعنصر الرابط التشعبي للمقالات


contentClass = None
infoClass = None
#اختياريه
# الكلاس الاب الذي بداخلة المقالة
#كلاس الذي يحتوي على بيانات الكاتب والتاريخ



#-------------------------------------------------------------------------#

excluded_url_words = ['authors', 'topics','author','tag','page']
# استبعاد الروابط -ليست مقالات - التي تحتوي على احداء هذه الكلمات


excluded_content_classes = ['option','toc','references','references-title','related-articles-list1','toggler-body','fs-x--5']
#كلاسات مستبعده من المقالة نفسها

excluded_content_words = {'قد يعجبك أيضا', 'الأكثر قراءة', 'شارك برأيك'}
 # استبعاد من محتوى المقالة الاسطر التي تحتوي على احدى هذه الكلمات




ChickUrlTarget(web_url,excluded_url_words,excluded_content_classes,excluded_content_words,alltopecClass,aClass,contentClass,infoClass)



