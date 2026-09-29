# Stable live menu hero

The existing menu used a 28-second 1→1.045 scale animation on the live harbor key art. The user reported that the screen recording shook instead of staying pixel stable. This pass removes the continuous hero transform while keeping its image and layout.

`pnpm exec tsx harness/menu-stability/capture.mts` rebuilt the normal web app and opened the real menu in silent, headless WebKit at **852×393, DPR 2**, with normal motion preferences. After the hero loaded and the menu settled, the script captured the same right-side art crop twice, **2.5 seconds** apart: [first](first.png) · [second](second.png). The two PNGs have the **same SHA-256**, `75aedb75d8910ee18cb0b20bdd0a420abe088eddcf4ac75adc3dc75185005da2`. The [machine report](report.json) records `animationName: none`, `transform: none`, opacity 1 and the same 852×393 rectangle in both samples, with zero page errors.

This proves stability for the live menu art in this WebKit run. The progress numbers and rings on the loading screen still animate by design, and the user's physical iPhone bottom strip and warm-start timing remain device checks.
