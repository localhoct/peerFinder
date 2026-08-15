# peerFinder

ابزار پایتون برای جمع آوری Peer های Cloudflare AS13335 از bgp.he.net.

## امکانات

- دریافت اطلاعات Peer ها
- ذخیره subnet ها به صورت فایل txt
- دسته بندی بر اساس کشور
- نام فایل برابر نام Peer
- دارای cache و retry برای جلوگیری از درخواست های زیاد

## نصب در Linux

```bash
sudo apt update
sudo apt install python3 python3-pip git -y

git clone https://github.com/localhoct/peerFinder.git
cd peerFinder

pip3 install -r requirements.txt

python3 main.py
```

## نصب در Termux Android

```bash
pkg update
pkg install python git -y

git clone https://github.com/localhoct/peerFinder.git
cd peerFinder

pip install -r requirements.txt

python main.py
```

## Output

فعلا پوشه output در مخزن قرار ندارد.

بعد از اجرا ساختار خروجی به شکل زیر خواهد بود:

```
output/
 ├── US/
 │    └── PEER.txt
 ├── DE/
 │    └── PEER.txt
 └── NL/
      └── PEER.txt
```

هر فایل فقط شامل subnet ها خواهد بود.

## Push کردن تغییرات شخصی

```bash
git add .
git commit -m "update peer data"
git push origin main
```

## توسعه آینده

- GeoIP country detection
- IPv4/IPv6 separation
- JSON export
- Scheduled updates
