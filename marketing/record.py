"""Record the 칼퇴 박대리 promo on a virtual clock. python3 record.py [preview|full]"""
import json, os, subprocess, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'out'); os.makedirs(os.path.join(OUT, 'stills'), exist_ok=True)
MODE = sys.argv[1] if len(sys.argv) > 1 else 'preview'
FPS, DT = 30, 1000 / 30
CLOCK = open(os.path.join(HERE, '..', 'zoo_video', 'record.py')).read().split('CLOCK = r"""')[1].split('"""')[0]
events, t_ms = [], 0.0

def main():
    global t_ms
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path='/usr/bin/google-chrome')
        page = browser.new_page(viewport={'width': 360, 'height': 640}, device_scale_factor=3)
        page.on('pageerror', lambda e: print('PAGE EXCEPTION:', e))
        page.add_init_script(CLOCK)
        page.goto('file://' + os.path.join(HERE, 'rec.html'))
        page.wait_for_timeout(300)
        ev = lambda code: page.evaluate('c => window.__K.ev(c)', code)
        cap = lambda html: page.evaluate('h => document.getElementById("cap").innerHTML = h', html)
        ff = None
        if MODE == 'full':
            ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', str(FPS), '-c:v', 'mjpeg', '-i', '-',
                                   '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '20', '-pix_fmt', 'yuv420p', '-r', str(FPS),
                                   os.path.join(OUT, 'promo_silent.tmp.mp4')], stdin=subprocess.PIPE)
        def frames(n, still=None, each=None):
            global t_ms
            for i in range(n):
                page.evaluate('() => window.__tick(%f)' % DT)
                g = ev("gates")
                if g > seen['gates']: seen['gates'] = g; mark('gate')
                if each: each(i)
                if ff: ff.stdin.write(page.screenshot(type='jpeg', quality=92))
                elif still and i == n - 1: page.screenshot(path=os.path.join(OUT, 'stills', still + '.png'))
                t_ms += DT
        seen = {'gates': 0}
        def mark(name): events.append([name, round(t_ms / 1000, 3)])
        def tap():
            page.evaluate("() => { const f = document.getElementById('finger'); f.style.display = 'block'; }")
            ev("heading = -heading; pressing = false;"); mark('tap')
            frames(4)
            page.evaluate("() => { document.getElementById('finger').style.display = 'none'; }")

        # helpers: drop things right in the runner's path, a given distance ahead
        ev("""window.ahead = (k, dy, extra = {}) => { const d = Math.max(60, speed * (1 - .3 * Math.abs(lean))); const x = clamp(px + vx * (dy / d), 40, 320);
                 objs.push(Object.assign({k, x, y: worldY + PY() + dy, s: 1, gap: 130, done: false}, extra)); return x; };
              Math.random = (() => { let s = 9; return () => (s = (s * 16807) % 2147483647) / 2147483647; })();
              nick = '박대리'; $('start').hidden = true; submitScore = async () => {}; logPlay = () => {};""")
        ev("newGame(); texts = []; nextSpawn = 1e12; objs = []; speed = 260; dist = 300; yeti = {gap: 70};")
        frames(2)

        # S0 hook: the boss right behind
        cap('6시 땡!<br><em>칼퇴 시작</em> 🏃')
        def hold_gap(g):
            return lambda i: ev(f"yeti.gap = {g}; texts = texts.filter(x => !x.text.includes('쫓아온다'))")
        frames(20, each=hold_gap(70))
        tap(); frames(14, each=hold_gap(75)); tap(); frames(18, still='s0', each=hold_gap(80))

        # S1 zig-zag through 칼퇴 gates
        cap('탭하면 지그재그<br><em>칼퇴 게이트 통과</em>')
        for k in range(3):
            ev("ahead('gate', 130)" + ("; ahead('fish', 70)" if k == 1 else ""))
            frames(14, each=hold_gap(100))
            tap(); frames(6 if k < 2 else 10, still='s1' if k == 2 else None, each=hold_gap(100))

        # S2 scooter = invincible
        cap('킥보드 타면<br><em>무적 질주</em> 🛴')
        ev("objs = objs.filter(o => o.y - worldY < PY() + 20); ahead('ramp', 110); ahead('rock', 230); ahead('tree', 300); ahead('rock', 380, {x: 0});")
        ev("objs[objs.length - 1].x = objs[objs.length - 2].x + 6")
        boosted = [False]
        def watch_boost(i):
            ev("yeti.gap = 110")
            if not boosted[0] and ev("boost > 0"): boosted[0] = True; mark('boost')
            if ev("objs.some(o => o.smashed && !o.marked && (o.marked = true))"): mark('smash')
        frames(60, still='s2', each=watch_boost)

        # S3 speed bump = trip
        cap('방지턱 걸리면<br><em>넘어짐 ㅋㅋ</em>')
        ev("boost = 0; inv = 0; objs = []; ahead('tree', 150);")
        crashed = [False]
        def watch_crash(i):
            if not crashed[0] and ev("tumble > 0"): crashed[0] = True; mark('crash')
        frames(48, still='s3', each=watch_crash)

        # S4 caught by the boss
        cap('부장님한테 잡히면<br><em>야근 확정</em> ㅋㅋ')
        over = [False]
        def watch_over(i):
            if not over[0] and ev("state !== 'play'"): over[0] = True; mark('caught')
        ev("yeti.gap = 45; tumble = .6; speed = 90;")
        frames(110, still='s4', each=watch_over)

        # S5 end card
        cap('')
        ev("""$('over').hidden = true; $('endcard').hidden = false;
              const c = $('endFace').getContext('2d'); c.clearRect(0, 0, 300, 300); c.fillStyle = '#dfe3ea'; c.beginPath(); c.arc(150, 150, 140, 0, 7); c.fill();
              drawFox(c, 150, 175, .2, 'happy', 1000, 5);""")
        mark('endcard')
        frames(96, still='s5')

        if ff:
            ff.stdin.close(); code = ff.wait()
            if code == 0: os.replace(os.path.join(OUT, 'promo_silent.tmp.mp4'), os.path.join(OUT, 'promo_silent.mp4'))
            print('ffmpeg exit', code)
        json.dump({'duration': round(t_ms / 1000, 3), 'events': events}, open(os.path.join(OUT, 'events.json'), 'w'), indent=1)
        print('duration', round(t_ms / 1000, 2), 's', events)
        browser.close()

main()
