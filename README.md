# CompaniesHouseGPT-Public
A research project for analysing the data held in the public domain at the UK Companies House register. Uses a combination of OCR, OpenAI's LLM APIs and Python.
# Overview
<h2>📌 Context</h2>
<ul>
  <li>The development of the OpenAI suite of Large Language Models (LLMs), specifically ChatGPT, in recent months has rapidly increased what can be done with AI</li>
  <li>One useful element of ChatGPT is the ability to extract significant information from text data that can be in an unstructured and irregular format. Often this information can be nuanced and is not possible to get via traditional programming methods.</li>
  <li>For example, ChatGPT can extract highly specific data in a JSON format of your chosing directly from text:</li>
  <img src='https://user-images.githubusercontent.com/90655952/230784239-e6602cd4-5b58-4dd4-827e-82d87a3baf09.png'></img>
  <li>Therefore, using ChatGPT, is it possible to extract information from the financial statements of companies by using OCR to extract the text and then scanning for an interpretation of the data you want?</li>
  <li>This project seeks to achieve this</li>
</ul>
<h2>📁 Installation</h2>
<h3>Prerequisites</h3
<p><b>In order to OCR documents please install the latest versions of these apps and add them to your system path</b><p>
<ul>
  <li>Poppler:
    <ul>
      <li>Windows: <a href='https://github.com/oschwartz10612/poppler-windows/releases/'>https://github.com/oschwartz10612/poppler-windows/releases/</a></li>
      <li>Ubuntu: sudo apt-get install poppler-utils</li>
      <li>Archlinux: sudo pacman -S poppler</li>
      <li>Ubuntu: brew install poppler</li>
    </ul>
  </li>
  <li>Tesseract: <a href='https://tesseract-ocr.github.io/tessdoc/Downloads.html'>https://tesseract-ocr.github.io/tessdoc/Downloads.html</a></li>
</ul>
<p><b>To run the code:</b></p>
<ul>
  <li>Install Python and add it to your system path<br><a href='https://www.python.org/downloads/'>https://www.python.org/downloads/</a></li>
  <li>Run 'setup.bat' or 'setup.sh'</li>
  <li>Sign in / Register at the UK Companies House API dashboard, create a new application and add your API key to 'main.py':<br><a href='https://developer.company-information.service.gov.uk/overview'>https://developer.company-information.service.gov.uk/overview</a></li>
  <li>Sign in / Register at OpenAI's API and save your API secret key to 'main.py'<br><a href='https://platform.openai.com/signup'>https://platform.openai.com/signup</a></li>
</ul>
<p>Now 'main.py' should look like this</p>

```python
if __name__ == "__main__":
    openai.api_key = "YOUR-OPENAI-API-KEY"
    CH.AUTH = ("YOUR-COMPANIES-HOUSE-API-KEY", '')
    main()
```

<p>This is now ready to run and can produce the save data as included in 'Auditor Count.csv' and 'Companies that Use Auditors.csv' 👍</p>