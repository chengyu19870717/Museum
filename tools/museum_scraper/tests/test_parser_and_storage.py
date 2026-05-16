from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from museum_scraper.config import CrawlConfig
from museum_scraper.models import ImageCandidate, MuseumSeed
from museum_scraper.parsing import MuseumPageParser
from museum_scraper.storage import MuseumStorage


SAMPLE_HTML = """
<html>
  <head>
    <title>示例博物馆简介</title>
    <meta name="description" content="这是一家示例博物馆，展示陶瓷与青铜器。">
  </head>
  <body>
    <main class="content">
      <h1>示例博物馆</h1>
      <p>示例博物馆位于北京市东城区示例路 8 号，开放时间为周二至周日 09:00-17:00。</p>
      <p>馆内设有常设展厅、数字展厅和馆藏珍品展区，长期展出青铜器与陶瓷文物。</p>
      <a href="/contact.html">联系我们</a>
      <a href="/about/venue.html">展馆介绍</a>
      <a href="/collections/list.html">馆藏珍品</a>
      <img src="/images/logo.png" alt="站点 logo">
      <img src="/images/hero.jpg" alt="博物馆外景">
      <img src="/images/wechat-qrcode.png" alt="微信服务号">
    </main>
  </body>
</html>
"""

CHN_CONTACT_HTML = """
<html>
  <head>
    <title>中国国家博物馆官方网站</title>
  </head>
  <body>
    <div class="cj_xw_tt">联系我们</div>
    <div class="cj_xw_cong">
      <div class="TRS_Editor">
        <p>参观咨询热线：010-65116400（9:00-16:30）</p>
        <p>通讯地址 北京市东城区东长安街16号 中国国家博物馆 邮编：100006</p>
        <p>社教活动预约：guoboshejiao@126.com</p>
      </div>
    </div>
  </body>
</html>
"""

CHN_SERVICE_HTML = """
<html>
  <head>
    <title>中国国家博物馆官方网站</title>
  </head>
  <body>
    <div class="fw_shmmlisjk" id="jiaotongili">
      <p>09:00 开馆时间</p>
      <p>16:00 停止入馆</p>
      <p>16:30 观众退场</p>
      <p>17:00 闭馆时间</p>
      <p>每周一例行闭馆，国家法定节假日除外</p>
      <p>中国国家博物馆 北京东城区东长安街16号 天安门广场东侧</p>
    </div>
    <div class="TRS_Editor">
      <p>本馆每日09:00—17:00（16:00停止入馆），周一闭馆（法定节假日除外）。</p>
    </div>
  </body>
</html>
"""

AUTH_NOISE_HTML = """
<html>
  <head>
    <title>登录 - 示例博物馆</title>
  </head>
  <body>
    <main class="content">
      <p>请输入正确邮箱地址，长度为8至16位，需包含数字及特殊符号。</p>
      <p>开放时间 在线订票 交通路线 参观须知</p>
      <a href="/passport/login.html">登录</a>
      <a href="/passport/login.html?type=register">注册</a>
      <a href="/visit.html">开放时间</a>
      <a href="/contact.html">联系我们</a>
    </main>
  </body>
</html>
"""

DPM_ABOUT_HTML = """
<html>
  <head>
    <title>总说 - 故宫博物院</title>
  </head>
  <body>
    <div class="always-wrap">
      <p>故宫博物院是一座特殊的博物馆，成立于1925年，建立在明清皇宫紫禁城的基础上。</p>
      <p>它是世界上规模最大、保存最完整的木结构宫殿建筑群。</p>
    </div>
  </body>
</html>
"""

DPM_VISIT_HTML = """
<html>
  <head>
    <title>导览 - 故宫博物院</title>
  </head>
  <body>
    <div class="visit2">
      <p>开放时间</p>
      <p>除法定节假日外，故宫博物院全年实行周一全天闭馆的措施。</p>
      <div class="box">
        <p>旺季 4.1-10.31</p>
        <p>开放入馆时间：8:30</p>
        <p>停止入馆时间：16:00</p>
        <p>珍宝馆、钟表馆停止入馆时间：16:10</p>
        <p>闭馆时间：17:00</p>
        <p>淡季 11.1-3.31</p>
        <p>开放入馆时间：8:30</p>
        <p>停止入馆时间：15:30</p>
        <p>珍宝馆、钟表馆停止入馆时间：15:40</p>
        <p>闭馆时间：16:30</p>
      </div>
    </div>
    <div class="visit5">
      <div class="p">咨询电话：400-950-1925</div>
    </div>
    <div class="footer">
      网站维护：故宫博物院数字与信息部 联系方式：gugong@dpm.org.cn
    </div>
  </body>
</html>
"""

DPM_CONTACT_HTML = """
<html>
  <head>
    <title>联系我们 - 故宫博物院</title>
    <meta name="Description" content="参观咨询：咨询电话：400-950-1925，服务时间：08:00-20:00。网站维护：故宫博物院数字与信息部电子邮件地址：gugong@dpm.org.cn 地址：北京市东城区景山前街4号 故宫博物院 邮编：100009">
  </head>
  <body></body>
</html>
"""

SCRIPT_NOISE_HTML = """
<html>
  <head><title>故宫博物院</title></head>
  <body>
    <main class="content">
      <p>这里是一个有真实正文内容的首页，不应该因为脚本里的点击事件被当成重定向页。</p>
    </main>
    <script>
      function logout() {
        window.location.href='/member/logout.html';
      }
    </script>
  </body>
</html>
"""


class ParserAndStorageTests(unittest.TestCase):
    def test_parser_extracts_summary_links_and_images(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        page = parser.parse("https://example-museum.cn/index.html", SAMPLE_HTML, depth=0)
        self.assertEqual(page.page_type, "overview")
        self.assertIn("示例博物馆位于北京市东城区示例路 8 号", page.text)
        self.assertEqual(page.metadata["address"], "位于北京市东城区示例路 8 号")
        self.assertEqual(page.metadata["opening_hours"], "开放时间为周二至周日 09:00-17:00")
        self.assertEqual(page.next_links[0], "https://example-museum.cn/contact.html")
        self.assertEqual(len(page.next_links), 3)
        self.assertEqual(page.images[0].url, "https://example-museum.cn/images/hero.jpg")
        self.assertEqual(len(page.images), 1)

    def test_storage_groups_files_by_museum_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = MuseumStorage(Path(temp_dir), "示例博物馆")
            storage.save_museum_metadata(
                MuseumSeed(name="示例博物馆", province="北京市"),
                [],
                "https://example-museum.cn/",
            )
            storage.save_image_bytes(
                ImageCandidate(
                    url="https://example-museum.cn/images/hero.jpg",
                    alt="博物馆外景",
                    source_page="https://example-museum.cn/index.html",
                    page_type="overview",
                ),
                b"fake-image-content",
                "image/jpeg",
            )
            self.assertTrue((Path(temp_dir) / "示例博物馆" / "museum.json").exists())
            image_dir = Path(temp_dir) / "示例博物馆" / "images" / "overview"
            self.assertTrue(any(image_dir.iterdir()))

    def test_site_extractor_cleans_contact_metadata(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        page = parser.parse(
            "https://www.chnmuseum.cn/shxg/lxwm/201901/t20190102_37017.shtml",
            CHN_CONTACT_HTML,
            depth=1,
        )
        self.assertEqual(page.page_type, "visit")
        self.assertEqual(page.title, "联系我们")
        self.assertEqual(page.metadata["phone"], "010-65116400")
        self.assertEqual(page.metadata["address"], "北京市东城区东长安街16号")
        self.assertEqual(page.metadata["email"], "guoboshejiao@126.com")

    def test_site_extractor_builds_opening_hours_from_service_page(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        page = parser.parse("https://www.chnmuseum.cn/cg/", CHN_SERVICE_HTML, depth=1)
        self.assertEqual(page.page_type, "visit")
        self.assertEqual(page.metadata["opening_hours"], "09:00-17:00（16:00停止入馆），周一闭馆（法定节假日除外）")
        self.assertEqual(page.metadata["address"], "北京市东城区东长安街16号 天安门广场东侧")

    def test_parser_skips_auth_links_and_invalid_metadata(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        page = parser.parse("https://example-museum.cn/login.html", AUTH_NOISE_HTML, depth=0)
        self.assertNotIn("address", page.metadata)
        self.assertNotIn("opening_hours", page.metadata)
        self.assertEqual(
            set(page.next_links),
            {
                "https://example-museum.cn/contact.html",
                "https://example-museum.cn/visit.html",
            },
        )

    def test_palace_museum_extractor_extracts_about_and_visit_content(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        about_page = parser.parse("https://www.dpm.org.cn/about/about_view.html", DPM_ABOUT_HTML, depth=1)
        visit_page = parser.parse("https://www.dpm.org.cn/Visit.html", DPM_VISIT_HTML, depth=1)
        self.assertEqual(about_page.title, "故宫博物院总说")
        self.assertIn("成立于1925年", about_page.text)
        self.assertEqual(visit_page.title, "故宫博物院导览")
        self.assertEqual(visit_page.metadata["phone"], "400-950-1925")
        self.assertEqual(
            visit_page.metadata["opening_hours"],
            "旺季4.1-10.31 8:30-17:00（16:00停止入馆，珍宝馆/钟表馆16:10停止入馆）；淡季11.1-3.31 8:30-16:30（15:30停止入馆，珍宝馆/钟表馆15:40停止入馆）；周一闭馆（法定节假日除外）",
        )
        self.assertEqual(visit_page.metadata["email"], "gugong@dpm.org.cn")

    def test_palace_museum_contact_page_extracts_address(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        page = parser.parse("https://www.dpm.org.cn/singles_detail/252829.html", DPM_CONTACT_HTML, depth=1)
        self.assertEqual(page.metadata["address"], "北京市东城区景山前街4号")
        self.assertEqual(page.metadata["phone"], "400-950-1925")
        self.assertEqual(page.metadata["email"], "gugong@dpm.org.cn")

    def test_client_redirect_ignores_event_handler_noise(self) -> None:
        parser = MuseumPageParser(CrawlConfig.default("output"))
        redirect = parser.extract_client_redirect("https://www.dpm.org.cn/", SCRIPT_NOISE_HTML)
        self.assertEqual(redirect, "")


if __name__ == "__main__":
    unittest.main()
