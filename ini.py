import requests
import os
from urllib.parse import urlparse

def download_php_file(url, save_dir="site"):
    """
    تحميل ملف PHP من رابط معين
    """
    try:
        # التأكد من صحة الرابط
        if not url.startswith(('http://', 'https://')):
            print("❌ الرابط يجب أن يبدأ بـ http:// أو https://")
            return False
        
        # إنشاء مجلد الحفظ
        os.makedirs(save_dir, exist_ok=True)
        
        # استخراج اسم الملف من الرابط
        parsed_url = urlparse(url)
        filename = os.path.basename(parsed_url.path)
        
        # إذا ما كان في اسم ملف، استخدم index.php
        if not filename or not filename.endswith('.php'):
            filename = "index.php"
        
        # طباعة معلومات التحميل
        print(f"📥 جاري تحميل: {filename}")
        print(f"🔗 من الرابط: {url}")
        
        # تحميل الملف
        r = requests.get(url, timeout=30)
        
        # التحقق من نجاح الطلب
        if r.status_code == 200:
            filepath = os.path.join(save_dir, filename)
            
            with open(filepath, "wb") as f:
                f.write(r.content)
            
            # عرض معلومات الملف
            file_size = len(r.content)
            print(f"✅ تم تحميل {filename} بنجاح")
            print(f"📁 المسار: {filepath}")
            print(f"📊 الحجم: {file_size} بايت ({file_size/1024:.2f} كيلوبايت)")
            return True
        else:
            print(f"❌ خطأ: الخادم رجع كود {r.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ انتهت مهلة الاتصال - الرابط بطيء أو لا يستجيب")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ فشل الاتصال - تأكد من اتصال الإنترنت والرابط")
        return False
    except Exception as e:
        print(f"❌ حدث خطأ: {str(e)}")
        return False

def main():
    """
    البرنامج الرئيسي
    """
    print("=" * 50)
    print("🔽 برنامج تحميل ملفات PHP")
    print("=" * 50)
    
    while True:
        # طلب الرابط من المستخدم
        url = input("\n📎 أدخل رابط ملف PHP (أو 'exit' للخروج): ").strip()
        
        # الخروج من البرنامج
        if url.lower() in ['exit', 'خروج', 'quit']:
            print("👋 مع السلامة!")
            break
        
        # تحميل الملف
        if url:
            download_php_file(url)
        else:
            print("⚠️ الرجاء إدخال رابط صحيح")
        
        # السؤال عن تحميل ملف آخر
        another = input("\n🔄 تريد تحميل ملف آخر؟ (y/n): ").strip().lower()
        if another not in ['y', 'yes', 'نعم', 'ن']:
            print("👋 مع السلامة!")
            break

if __name__ == "__main__":
    main()
