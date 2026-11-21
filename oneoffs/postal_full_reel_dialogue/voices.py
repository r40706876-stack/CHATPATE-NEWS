import json
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

folder = Path(__file__).resolve().parent
sys.path.insert(0, str(folder.parent / "postal_recruitment_two_voices"))
import render as voices

if len(sys.argv) == 2:
    voices.OUT.mkdir(exist_ok=True)
    voices.DIALOGUE = json.loads(r'''[["golu","मतलब पोस्टमैन का पेपर देने के लिए पहले एम टी एस नहीं बनना पड़ेगा?"],["bhaiya","जी डी एस से सीधे परीक्षा का रास्ता पहले से है। बदलाव इंतज़ार में है।"],["bhaiya","पोस्टमैन और मेल गार्ड, दोनों के लिए पाँच की जगह तीन साल की नियमित सेवा का प्रस्ताव है।"],["golu","तो भैया, मैं भर्ती का नोटिफिकेशन आने तक रुकूँ?"],["bhaiya","पेपर कब दे पाओगे, ये भर्ती का नोटिफिकेशन बताएगा। लेकिन तैयारी के लिए उसका इंतज़ार क्यों करना?"],["bhaiya","ड्राफ्ट मंज़ूर हुआ और भर्ती निकली, तो तैयारी के लिए वक्त कम पड़ सकता है।"],["golu","फिर आज शुरुआत कहाँ से करूँ?"],["bhaiya","पोस्टल एज डॉट इन पर हमारे वीडियो कोर्स का फ्री डेमो देखो।"],["bhaiya","क्लास में नियम आसान भाषा और चित्रों से समझाए जाते हैं, ताकि वहीं याद हो जाएँ और रटना न पड़े।"]]''')
    voices.voice_parts(sys.argv[1])
else:
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(lambda role: subprocess.run([sys.executable, __file__, role], check=True), ("golu", "bhaiya")))
