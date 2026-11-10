<p align="center">
  <img src="data/icons/hicolor/scalable/apps/io.github.openapi.Gknowledge.svg" alt="" width="96">
</p>

<h1 align="center">gknowledge</h1>

<p align="center"><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a> · <a href="README.it.md">Italiano</a> · <b>Français</b> · <a href="README.pt-BR.md">Português (BR)</a> · <a href="README.es.md">Español</a> . <a href="README.bn.md">বাংলা</a></p>

<p align="center">
  <b>কার্পেথির এলএলএম উইকি : নেটিভ GNOME অ্যাপ হিসেবে</b><br>
  লিঙ্কড উইকি আপনার ডকুমেন্ট থেকে, যা আপডেট হবে এলএলএম দ্বারা।<br>
  নেটিভ GNOME অ্যাপ। বাই ডিফল্ট অফলাইন, প্লেইন মার্কডাউন অন ডিস্ক, অবসিডিয়ান কমপ্যাটিবেল।
     
</p>

<p align="center">
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/github/license/openapi/gknowledge?style=for-the-badge&color=3584e4"></a>
  <img alt="GTK 4" src="https://img.shields.io/badge/GTK-4-4a86cf?style=for-the-badge&logo=gtk&logoColor=white">
  <img alt="Ubuntu 24.04+" src="https://img.shields.io/badge/Ubuntu-24.04%2B-E95420?style=for-the-badge&logo=ubuntu&logoColor=white">
  <a href="https://github.com/openapi/gknowledge/releases/latest"><img alt="Release" src="https://img.shields.io/github/v/release/openapi/gknowledge?style=for-the-badge&color=E95420"></a>
</p>

<p align="center">
  <img src="docs/gknowledge-demo.svg" alt="gknowledge en action : importer des articles d'IA, obtenir un wiki lié, poser des questions avec citations" width="880">
</p>

## Installation

উবুন্টু ২৪.০৪ এবং ডেবিয়ান ১৩+ এ ইনস্টল করতে নিচের কমান্ড ব্যবহার করুন এবং যোগ করুন সাইন্ড gknowledge APT রিপোজিটরি। এর ফলে `apt upgrade` এর মাধ্যমে আপডেট চলে আসবে। (অন্য ডিস্ট্রিবিউশন এর ক্ষেত্রে ইনস্টলেশন ঘটবে `~/.local` ডিরেকটরিতে ) :

```bash
curl -fsSL https://github.com/openapi/gknowledge/releases/latest/download/install.sh | bash
```

অথবা নিজেই যোগ করুন APT রিপোজিটরি:

```bash
sudo curl -fsSLo /usr/share/keyrings/gknowledge.gpg https://openapi.github.io/gknowledge/gknowledge.gpg
sudo curl -fsSLo /etc/apt/sources.list.d/gknowledge.sources https://openapi.github.io/gknowledge/gknowledge.sources
sudo apt update && sudo apt install gknowledge
```

ফ্ল্যাটপ্যাক এর মাধ্যমে যেকোন ডিস্ট্রিবিউশনে ইনস্টল করার কমান্ড (GNOME রানটাইম ফ্ল্যাটহাব থেকে):

```bash
flatpak install --user https://openapi.github.io/gknowledge/io.github.openapi.Gknowledge.flatpakref
```

## অফলাইন ব্যবহারের জন্য ডিজাইনকৃত

gknowledge একবার ইনস্টল করার পর ইন্টারনেট কানেকশন, একাউন্ট বা পেইড এপিআই - কোনোটাই প্রয়োজন নেই।

- **বিল্ট ইন অফলাইন ইঞ্জিন** : 
ডকুমেন্ট ইমপোর্ট, উইকি এবং সাইটেশন সহ উত্তর - সবকিছুই কাজ করবে কোনও এআই মডেল ছাড়াই। 
- **মোবাইল ডেটার ন্যূনতম ব্যবহার** : বাই ডিফল্ট কোনো কিছুই ক্লাউডে প্রেরিত হয় না। যদি আপনি মডেল ব্যবহার করতে চান, [Ollama](https://ollama.com) লোকালি রান হবে, যা ডাউনলোড হবে শুধু একবার। 
- **স্বল্প হার্ডওয়্যার চাহিদা** : পাইথনে লেখা নেটিভ GTK অ্যাপ্লিকেশন, Electron বা এমবেডেড ব্রাউজার ছাড়াই, যা যেকোনো সাধারণ লিনাক্স ল্যাপটপে চালানো সম্ভব। 
- **আপনার ডাটা আপনার কাছেই** : মার্কডাউন ফাইলস এবং SQLite ইনডেক্স, আপনার নিয়ন্ত্রণাধীন ফোল্ডারে সংরক্ষিত। 

## gknowledge কেন
 
আপনি যদি [LLM Wiki](https://github.com/nashsu/llm_wiki), [Tolaria](https://github.com/refactoringhq/tolaria), [Reor](https://github.com/reorproject/reor) অথবা [Khoj](https://github.com/khoj-ai/khoj) ব্যবহার করে থাকেন, আপনি ইতোমধ্যে এই লুপ সম্পর্কে জানেন : **তথ্যের উৎস ইনজেস্ট করা, সেটা থেকে মডেল দ্বারা উইকি বানানো ও মেইনটেইন করা, উইকি থেকে প্রশ্নোত্তরের মাধ্যমে জানা।** gknowledge ঠিক একই কাজ করে, নোম অ্যাপ হিসেবে। 

- **নেটিভ অ্যাপ**, GTK 4 এবং Libadwaita : Electron, Tauri, বা ব্রাউজার ইঞ্জিন ছাড়াই।  
- **একাউন্ট ছাড়াই ব্যবহারযোগ্য** : বিল্ট ইন হিউরিস্টিক ইঞ্জিন অফলাইনে তথ্য ইনজেস্ট করে উত্তর দেয়। উন্নততর অভিজ্ঞতার জন্য মডেল যোগ করা যায়।   
- **সোর্স ও রিভিউ** : জেনারেটেড পেইজ সমূহ সোর্স রেকর্ড করে এবং উত্তর সমূহে সেসব পেইজ এর উল্লেখ থাকে। রিভিউ কিউ এর মাধমে নিয়ন্ত্রণ থাকে আপনার হাতে। 

## Claude Code, Codex অথবা Cursor থেকে ব্যবহার

```bash
claude mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project     # Claude Code
codex mcp add gknowledge -- gknowledge-mcp ~/Knowledge/my-project      # Codex CLI
```

এর মাধ্যমে এজেন্টটি উইকি সার্চ করতে পারে, পেইজ পড়তে পারে, সাইটেশন সহ প্রশ্ন জিজ্ঞাসা করতে পারে এবং নতুন উৎস যোগ করতে পারে। 

## বেছে নিন আপনার টুলের "মস্তিষ্ক"

| প্রোভাইডার  | যা দরকার | নোটস |
|---|---|---|
| **অফলাইন** (বাই ডিফল্ট) | নেই | Heuristic ভিত্তিক তথ্য নিষ্কাষণ এবং উত্তর প্রদান, সম্পূর্ণ ব্যক্তিগত|
| **ওলামা  / এলএম ষ্টুডিও  / ভিএলএএলএম** | লোকাল সার্ভার | ব্যবহারকারীর মেশিনে যে কোনো ওপেন এআই কমপ্যাটিবেল এন্ডপয়েন্ট |
| **চ্যাটজিপিটি** | প্লাস অথবা প্রো একাউন্ট | পছন্দ মতো প্রোভাইডার, *ChatGPT তে সাইন ইন করুন*। ইউসেজ চার্জ ইউজার প্ল্যান অনুযায়ী, কোনো এপিআই কী প্রয়োজন নেই |
| **ওপেন এআই কম্পাটবেল ক্লাউড** | এপিআই কী | ওপেন এআই, ওপেন রাউটার, টুগেদার বা অনুরূপ   |

## অবদান 

আপনাদের অবদান সাদরে আমন্ত্রিত: এখানে  [*good first issues*](https://github.com/openapi/gknowledge/labels/good%20first%20issue) সম্পর্কে জানুন। আফ্রিকান ভাষাসহ অন্যান্য ভাষায় অনুবাদ সম্পর্কিত অবদান বিশেষভাবে সমাদৃত। 

ডকুমেন্টেশন এর বাকি অংশ পাওয়া যাবে [ইংরেজি README তে](README.md). আপনি যদি gknowledge থেকে উপকৃত হোন, তাহলে ⭐ দিয়ে অন্যদের এটি খুঁজে পেতে সহায়তা করুন। 
