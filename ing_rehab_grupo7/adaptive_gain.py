"""
╔══════════════════════════════════════════════════════════════════╗
║  MÓDULO: Ganancia Adaptativa para Hemiparesia                   ║
║  Área: Control Motor y Acceso                                   ║
║  Genera: /results/session_<timestamp>.json                      ║
║  Estética: Soft Medical / Healthcare                            ║
╚══════════════════════════════════════════════════════════════════╝

CÓMO FUNCIONA:
1. CALIBRACIÓN: El paciente mueve el mouse libremente 5s → se mide su ROM real
2. TAREA DE ALCANCE: Aparecen targets circulares que debe alcanzar y clickear
3. GANANCIA ADAPTATIVA: Si el ROM es chico, el cursor se amplifica (gain > 1).
   Cada N trials exitosos, el gain baja un poco (desafío progresivo).
   Si falla mucho, el gain sube para facilitar.
4. EXPORTA JSON con todos los eventos, tiempos, trayectorias y gain por trial.

Dependencias: pip install pygame
Ejecutar: py adaptive_gain.py
"""

import pygame
import sys
nombre_paciente = sys.argv[1]
import os
import json
import math
import time
import random
from datetime import datetime

# ─── CONFIG ────────────────────────────────────────────────────────
SCREEN_W, SCREEN_H = 1024, 768
FPS = 60
TARGET_RADIUS = 45
NUM_TRIALS = 15
CALIBRATION_DURATION = 5.0

INITIAL_GAIN = 1.0
GAIN_MIN = 0.5
GAIN_MAX = 5.0
GAIN_DECREASE = 0.05
GAIN_INCREASE = 0.1
SUCCESS_STREAK_TO_DECREASE = 2
TRIAL_TIMEOUT = 10.0

# ─── PALETA HEALTHCARE (zona de prueba) ───────────────────────────
HC_BG = (224, 236, 222)
HC_SAGE = (118, 147, 130)
HC_TEAL = (44, 105, 117)
HC_MINT = (104, 130, 160)
HC_CREAM = (243, 239, 227)
HC_LIGHT = (192, 195, 185)
HC_WHITE = (250, 250, 247)
HC_DARK = (55, 70, 62)
HC_SUCCESS = (86, 160, 120)
HC_ERROR = (190, 100, 90)
HC_HIGHLIGHT = (205, 224, 201)

# ─── PALETA INICIO/RESULTADOS ────────────────────────────────────
IR_BG = (44, 105, 117)
IR_BG_DARK = (35, 85, 95)
IR_TEXT = (243, 239, 227)
IR_ACCENT = (205, 224, 201)
IR_HIGHLIGHT = (224, 236, 222)
IR_SUBTLE = (118, 147, 130)
IR_WARM = (220, 200, 170)

# ─── HELPERS ───────────────────────────────────────────────────────

def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def random_target_pos(margin=100):
    x = random.randint(margin, SCREEN_W - margin)
    y = random.randint(margin + 80, SCREEN_H - margin)
    return (x, y)

def draw_text(surf, text, pos, font, color=HC_DARK, center=False):
    rendered = font.render(text, True, color)
    rect = rendered.get_rect()
    if center:
        rect.center = pos
    else:
        rect.topleft = pos
    surf.blit(rendered, rect)

def draw_rounded_rect(surf, color, rect, radius=15):
    pygame.draw.rect(surf, color, rect, border_radius=radius)

def lerp_color(c1, c2, t):
    t = clamp(t, 0, 1)
    return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))

# ─── FASE 1: CALIBRACIÓN ──────────────────────────────────────────

def run_calibration(screen, clock, fonts):
    positions = []
    start = time.time()
    pygame.mouse.set_pos(SCREEN_W // 2, SCREEN_H // 2)

    while True:
        elapsed = time.time() - start
        remaining = max(0, CALIBRATION_DURATION - elapsed)

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                pygame.quit(); sys.exit()

        mx, my = pygame.mouse.get_pos()
        positions.append((mx, my))

        screen.fill(HC_BG)

        panel_rect = (SCREEN_W // 2 - 280, 40, 560, 220)
        draw_rounded_rect(screen, HC_WHITE, panel_rect, 20)

        draw_text(screen, "Calibración", (SCREEN_W // 2, 75),
                  fonts["title"], HC_TEAL, center=True)
        draw_text(screen, "Mové el mouse lo más que puedas",
                  (SCREEN_W // 2, 125), fonts["medium"], HC_DARK, center=True)
        draw_text(screen, "en todas las direcciones",
                  (SCREEN_W // 2, 155), fonts["medium"], HC_SAGE, center=True)

        draw_text(screen, f"{remaining:.0f}s", (SCREEN_W // 2, 210),
                  fonts["big_number"], HC_TEAL, center=True)

        bar_w = 400
        bar_h = 14
        bar_x = (SCREEN_W - bar_w) // 2
        bar_y = 245
        progress = elapsed / CALIBRATION_DURATION
        draw_rounded_rect(screen, HC_LIGHT, (bar_x, bar_y, bar_w, bar_h), 7)
        if progress > 0.01:
            draw_rounded_rect(screen, HC_SAGE,
                              (bar_x, bar_y, int(bar_w * min(progress, 1.0)), bar_h), 7)

        trail_len = len(positions)
        if trail_len > 1:
            start_idx = max(0, trail_len - 200)
            for i in range(start_idx + 1, trail_len):
                alpha_t = (i - start_idx) / (trail_len - start_idx)
                color = lerp_color(HC_LIGHT, HC_TEAL, alpha_t)
                thickness = max(1, int(3 * alpha_t))
                pygame.draw.line(screen, color, positions[i-1], positions[i], thickness)

        pygame.draw.circle(screen, HC_TEAL, (mx, my), 12)
        pygame.draw.circle(screen, HC_WHITE, (mx, my), 12, 3)
        pygame.draw.circle(screen, HC_WHITE, (mx, my), 4)

        pygame.display.flip()
        clock.tick(FPS)

        if elapsed >= CALIBRATION_DURATION:
            break

    if len(positions) < 2:
        return 50

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    rom_pixels = max(max(xs) - min(xs), max(ys) - min(ys))
    return max(rom_pixels, 10)


def calculate_initial_gain(rom_pixels):
    gain = 500 / max(rom_pixels, 10)
    return clamp(gain, GAIN_MIN, GAIN_MAX)


# ─── FASE 2: TAREA DE ALCANCE ─────────────────────────────────────

def run_trials(screen, clock, fonts, initial_gain):
    trials_data = []
    current_gain = initial_gain
    success_streak = 0
    virtual_x, virtual_y = SCREEN_W // 2, SCREEN_H // 2
    prev_raw = pygame.mouse.get_pos()

    for trial_num in range(NUM_TRIALS):
        target_pos = random_target_pos()
        trajectory = []
        start_time = time.time()
        hit = False
        errors = 0

        pygame.mouse.set_pos(SCREEN_W // 2, SCREEN_H // 2)
        prev_raw = (SCREEN_W // 2, SCREEN_H // 2)
        virtual_x, virtual_y = SCREEN_W // 2, SCREEN_H // 2

        while True:
            dt = clock.tick(FPS) / 1000.0
            elapsed = time.time() - start_time
            timed_out = elapsed >= TRIAL_TIMEOUT

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    pygame.quit(); sys.exit()
                if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
                    if dist((virtual_x, virtual_y), target_pos) <= TARGET_RADIUS:
                        hit = True
                    else:
                        errors += 1

            raw_pos = pygame.mouse.get_pos()
            dx = raw_pos[0] - prev_raw[0]
            dy = raw_pos[1] - prev_raw[1]
            prev_raw = raw_pos

            virtual_x += dx * current_gain
            virtual_y += dy * current_gain
            virtual_x = clamp(virtual_x, 0, SCREEN_W)
            virtual_y = clamp(virtual_y, 0, SCREEN_H)

            if len(trajectory) == 0 or pygame.time.get_ticks() % 3 == 0:
                trajectory.append({
                    "t": round(elapsed, 3),
                    "x": round(virtual_x, 1),
                    "y": round(virtual_y, 1),
                    "raw_x": raw_pos[0],
                    "raw_y": raw_pos[1]
                })

            screen.fill(HC_BG)

            # HUD
            hud_rect = (15, 10, SCREEN_W - 30, 60)
            draw_rounded_rect(screen, HC_WHITE, hud_rect, 15)
            draw_text(screen, f"Prueba {trial_num + 1} de {NUM_TRIALS}",
                      (35, 28), fonts["medium"], HC_DARK)
            draw_text(screen, f"Ganancia: {current_gain:.1f}x",
                      (300, 28), fonts["medium"], HC_TEAL)

            time_ratio = elapsed / TRIAL_TIMEOUT
            time_color = HC_DARK if time_ratio < 0.6 else (HC_ERROR if time_ratio > 0.85 else HC_SAGE)
            draw_text(screen, f"{elapsed:.1f}s", (530, 28), fonts["medium"], time_color)

            if errors > 0:
                draw_text(screen, f"Clicks errados: {errors}",
                          (650, 28), fonts["small"], HC_ERROR)

            dot_start_x = SCREEN_W - 200
            for i in range(NUM_TRIALS):
                dx_dot = dot_start_x + i * 12
                color = HC_SAGE if i < trial_num else (HC_TEAL if i == trial_num else HC_LIGHT)
                pygame.draw.circle(screen, color, (dx_dot, 40), 4)

            # Target
            pulse = abs(math.sin(elapsed * 2)) * 0.3 + 0.7
            halo_color = lerp_color(HC_BG, HC_SAGE, pulse * 0.4)
            pygame.draw.circle(screen, halo_color, target_pos, int(TARGET_RADIUS + 20))
            pygame.draw.circle(screen, HC_SAGE, target_pos, TARGET_RADIUS)
            pygame.draw.circle(screen, HC_WHITE, target_pos, TARGET_RADIUS, 3)
            pygame.draw.circle(screen, HC_HIGHLIGHT, target_pos, TARGET_RADIUS - 10, 2)
            pygame.draw.circle(screen, HC_WHITE, target_pos, 8)
            pygame.draw.circle(screen, HC_SAGE, target_pos, 4)

            d = dist((virtual_x, virtual_y), target_pos)
            if d > TARGET_RADIUS * 2:
                pygame.draw.line(screen, HC_LIGHT,
                                 (int(virtual_x), int(virtual_y)), target_pos, 1)

            on_target = d <= TARGET_RADIUS
            cursor_color = HC_SUCCESS if on_target else HC_TEAL
            pygame.draw.circle(screen, HC_LIGHT,
                               (int(virtual_x) + 2, int(virtual_y) + 2), 14)
            pygame.draw.circle(screen, cursor_color,
                               (int(virtual_x), int(virtual_y)), 12)
            pygame.draw.circle(screen, HC_WHITE,
                               (int(virtual_x), int(virtual_y)), 12, 3)
            cx, cy = int(virtual_x), int(virtual_y)
            pygame.draw.line(screen, HC_WHITE, (cx - 18, cy), (cx + 18, cy), 2)
            pygame.draw.line(screen, HC_WHITE, (cx, cy - 18), (cx, cy + 18), 2)

            draw_text(screen, "Alcanzá el círculo y hacé click",
                      (SCREEN_W // 2, SCREEN_H - 35), fonts["small"], HC_SAGE, center=True)

            pygame.display.flip()

            if hit or timed_out:
                break

        reaction_time = round(time.time() - start_time, 3)

        if hit:
            success_streak += 1
            if success_streak >= SUCCESS_STREAK_TO_DECREASE:
                current_gain = clamp(current_gain - GAIN_DECREASE, GAIN_MIN, GAIN_MAX)
                success_streak = 0
        else:
            success_streak = 0
            current_gain = clamp(current_gain + GAIN_INCREASE, GAIN_MIN, GAIN_MAX)

        path_length = 0
        for i in range(1, len(trajectory)):
            path_length += dist(
                (trajectory[i]["x"], trajectory[i]["y"]),
                (trajectory[i-1]["x"], trajectory[i-1]["y"])
            )

        direct_dist = dist((trajectory[0]["x"], trajectory[0]["y"]), target_pos) if trajectory else 0
        efficiency = round(direct_dist / max(path_length, 1), 3)

        trials_data.append({
            "trial": trial_num + 1,
            "target_x": target_pos[0],
            "target_y": target_pos[1],
            "hit": hit,
            "reaction_time_s": reaction_time,
            "errors": errors,
            "gain_used": round(current_gain, 3),
            "path_length_px": round(path_length, 1),
            "direct_distance_px": round(direct_dist, 1),
            "efficiency_ratio": efficiency,
            "trajectory_points": len(trajectory),
            "trajectory": trajectory
        })

        # Feedback
        screen.fill(HC_BG)
        panel = (SCREEN_W // 2 - 200, SCREEN_H // 2 - 80, 400, 160)
        draw_rounded_rect(screen, HC_WHITE, panel, 20)
        if hit:
            draw_text(screen, "Alcanzado", (SCREEN_W // 2, SCREEN_H // 2 - 30),
                      fonts["title"], HC_SUCCESS, center=True)
            draw_text(screen, f"{reaction_time:.1f} segundos",
                      (SCREEN_W // 2, SCREEN_H // 2 + 25), fonts["medium"], HC_SAGE, center=True)
        else:
            draw_text(screen, "Tiempo agotado", (SCREEN_W // 2, SCREEN_H // 2 - 30),
                      fonts["title"], HC_ERROR, center=True)
            draw_text(screen, "No te preocupes, seguimos",
                      (SCREEN_W // 2, SCREEN_H // 2 + 25), fonts["small"], HC_SAGE, center=True)

        pygame.display.flip()
        pygame.time.wait(1000)

    return trials_data, current_gain


# ─── PANTALLA INICIO ──────────────────────────────────────────────

def show_start_screen(screen, clock, fonts):
    waiting = True
    start_t = time.time()

    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

        elapsed = time.time() - start_t
        screen.fill(IR_BG)
        draw_rounded_rect(screen, IR_BG_DARK, (40, 40, SCREEN_W - 80, SCREEN_H - 80), 30)
        pygame.draw.line(screen, IR_SUBTLE, (80, 100), (SCREEN_W - 80, 100), 1)

        draw_text(screen, "Ganancia", (SCREEN_W // 2, 170), fonts["huge"], IR_TEXT, center=True)
        draw_text(screen, "Adaptativa", (SCREEN_W // 2, 240), fonts["huge"], IR_ACCENT, center=True)
        draw_text(screen, "Módulo de Control Motor", (SCREEN_W // 2, 320),
                  fonts["title"], IR_WARM, center=True)
        draw_text(screen, "Evaluación para Hemiparesia", (SCREEN_W // 2, 365),
                  fonts["medium_lg"], IR_HIGHLIGHT, center=True)
        draw_text(screen, "Este test mide y adapta la sensibilidad",
                  (SCREEN_W // 2, 440), fonts["medium"], IR_TEXT, center=True)
        draw_text(screen, "del mouse según tu rango de movimiento.",
                  (SCREEN_W // 2, 475), fonts["medium"], IR_TEXT, center=True)

        pygame.draw.line(screen, IR_SUBTLE, (300, 520), (SCREEN_W - 300, 520), 1)

        pulse = abs(math.sin(elapsed * 2)) * 0.15 + 0.85
        btn_color = lerp_color(IR_SUBTLE, IR_ACCENT, pulse)
        btn_rect = (SCREEN_W // 2 - 180, 555, 360, 65)
        draw_rounded_rect(screen, btn_color, btn_rect, 15)
        draw_text(screen, "Click para comenzar", (SCREEN_W // 2, 587),
                  fonts["medium_lg"], IR_BG, center=True)

        draw_text(screen, "IR 2026 · Control Motor y Acceso",
                  (SCREEN_W // 2, SCREEN_H - 70), fonts["small"], IR_SUBTLE, center=True)

        pygame.display.flip()
        clock.tick(30)


def show_calibration_result(screen, clock, fonts, rom_pixels, initial_gain):
    screen.fill(IR_BG)
    draw_rounded_rect(screen, IR_BG_DARK, (40, 40, SCREEN_W - 80, SCREEN_H - 80), 30)

    draw_text(screen, "Calibración Completa", (SCREEN_W // 2, 150),
              fonts["huge"], IR_ACCENT, center=True)
    pygame.draw.line(screen, IR_SUBTLE, (250, 210), (SCREEN_W - 250, 210), 1)

    draw_text(screen, "Rango de movimiento detectado:",
              (SCREEN_W // 2, 280), fonts["medium_lg"], IR_TEXT, center=True)
    draw_text(screen, f"{rom_pixels:.0f} píxeles",
              (SCREEN_W // 2, 340), fonts["huge"], IR_WARM, center=True)
    draw_text(screen, "Ganancia inicial asignada:",
              (SCREEN_W // 2, 420), fonts["medium_lg"], IR_TEXT, center=True)
    draw_text(screen, f"{initial_gain:.1f}x",
              (SCREEN_W // 2, 480), fonts["huge"], IR_HIGHLIGHT, center=True)

    btn_rect = (SCREEN_W // 2 - 180, 560, 360, 65)
    draw_rounded_rect(screen, IR_ACCENT, btn_rect, 15)
    draw_text(screen, "Iniciar prueba", (SCREEN_W // 2, 592),
              fonts["medium_lg"], IR_BG, center=True)

    pygame.display.flip()

    waiting = True
    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                waiting = False
        clock.tick(30)


# ─── PANTALLA RESULTADOS ─────────────────────────────────────────

def show_summary(screen, clock, fonts, session_data):
    trials = session_data["trials"]
    hits = sum(1 for t in trials if t["hit"])
    avg_rt = sum(t["reaction_time_s"] for t in trials if t["hit"]) / max(hits, 1)
    avg_eff = sum(t["efficiency_ratio"] for t in trials if t["hit"]) / max(hits, 1)
    gi = session_data['calibration']['initial_gain']
    gf = session_data['calibration']['final_gain']

    waiting = True
    while waiting:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                waiting = False
            if ev.type == pygame.KEYDOWN or ev.type == pygame.MOUSEBUTTONDOWN:
                waiting = False

        screen.fill(IR_BG)
        draw_rounded_rect(screen, IR_BG_DARK, (40, 40, SCREEN_W - 80, SCREEN_H - 80), 30)

        draw_text(screen, "Resultados", (SCREEN_W // 2, 100),
                  fonts["huge"], IR_ACCENT, center=True)
        pygame.draw.line(screen, IR_SUBTLE, (200, 145), (SCREEN_W - 200, 145), 1)

        y = 190
        draw_text(screen, f"{hits} de {len(trials)} alcanzados",
                  (SCREEN_W // 2, y), fonts["title"], IR_WARM, center=True)
        y += 70

        col_left = SCREEN_W // 2 - 200
        col_right = SCREEN_W // 2 + 50

        draw_text(screen, "Tiempo promedio", (col_left, y), fonts["medium"], IR_TEXT)
        draw_text(screen, f"{avg_rt:.1f}s", (col_right, y), fonts["title"], IR_HIGHLIGHT)
        y += 55

        draw_text(screen, "Eficiencia", (col_left, y), fonts["medium"], IR_TEXT)
        draw_text(screen, f"{avg_eff:.0%}", (col_right, y), fonts["title"], IR_HIGHLIGHT)
        y += 55

        draw_text(screen, "Gain inicial", (col_left, y), fonts["medium"], IR_TEXT)
        draw_text(screen, f"{gi:.1f}x", (col_right, y), fonts["title"], IR_HIGHLIGHT)
        y += 55

        draw_text(screen, "Gain final", (col_left, y), fonts["medium"], IR_TEXT)
        draw_text(screen, f"{gf:.1f}x", (col_right, y), fonts["title"], IR_HIGHLIGHT)
        y += 70

        pygame.draw.line(screen, IR_SUBTLE, (200, y - 15), (SCREEN_W - 200, y - 15), 1)

        if gf < gi:
            msg = "El paciente mejoró durante la sesión"
            detail = f"La ganancia bajó {gi - gf:.2f} puntos"
            color = IR_ACCENT
        elif gf > gi:
            msg = "Sesión con dificultad elevada"
            detail = f"La ganancia subió {gf - gi:.2f} puntos"
            color = IR_WARM
        else:
            msg = "Rendimiento estable"
            detail = "La ganancia se mantuvo sin cambios"
            color = IR_TEXT

        draw_text(screen, msg, (SCREEN_W // 2, y + 15), fonts["medium_lg"], color, center=True)
        draw_text(screen, detail, (SCREEN_W // 2, y + 50), fonts["medium"], IR_SUBTLE, center=True)

        draw_text(screen, "Datos guardados en /results  ·  Presioná cualquier tecla",
                  (SCREEN_W // 2, SCREEN_H - 65), fonts["small"], IR_SUBTLE, center=True)

        pygame.display.flip()
        clock.tick(30)


# ─── EXPORTACIÓN JSON ─────────────────────────────────────────────

def export_json(session_data):
    os.makedirs("results", exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join("results", f"session_{ts}.json")
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=2, ensure_ascii=False)
    print(f"[OK] Sesión exportada: {filepath}")
    return filepath


# ─── MAIN ──────────────────────────────────────────────────────────

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Ganancia Adaptativa · Control Motor")
    clock = pygame.time.Clock()
    pygame.mouse.set_visible(False)

    fonts = {
        "huge":       pygame.font.SysFont("Segoe UI", 52, bold=True),
        "big_number": pygame.font.SysFont("Segoe UI", 48, bold=True),
        "title":      pygame.font.SysFont("Segoe UI", 34, bold=True),
        "medium_lg":  pygame.font.SysFont("Segoe UI", 26),
        "medium":     pygame.font.SysFont("Segoe UI", 22),
        "small":      pygame.font.SysFont("Segoe UI", 17),
    }

    show_start_screen(screen, clock, fonts)

    rom_pixels = run_calibration(screen, clock, fonts)
    initial_gain = calculate_initial_gain(rom_pixels)

    show_calibration_result(screen, clock, fonts, rom_pixels, initial_gain)

    trials_data, final_gain = run_trials(screen, clock, fonts, initial_gain)

    session_data = {
        "module": "adaptive_gain",
        "area": "control_motor_hemiparesia",
        "timestamp": datetime.now().isoformat(),
        "config": {
            "num_trials": NUM_TRIALS,
            "trial_timeout_s": TRIAL_TIMEOUT,
            "target_radius_px": TARGET_RADIUS,
            "screen_resolution": [SCREEN_W, SCREEN_H],
            "gain_params": {
                "min": GAIN_MIN,
                "max": GAIN_MAX,
                "decrease_step": GAIN_DECREASE,
                "increase_step": GAIN_INCREASE,
                "success_streak_threshold": SUCCESS_STREAK_TO_DECREASE
            }
        },
        "calibration": {
            "duration_s": CALIBRATION_DURATION,
            "rom_pixels": round(rom_pixels, 1),
            "initial_gain": round(initial_gain, 3),
            "final_gain": round(final_gain, 3),
            "gain_delta": round(initial_gain - final_gain, 3)
        },
        "summary": {
            "total_trials": len(trials_data),
            "hits": sum(1 for t in trials_data if t["hit"]),
            "misses": sum(1 for t in trials_data if not t["hit"]),
            "avg_reaction_time_s": round(
                sum(t["reaction_time_s"] for t in trials_data if t["hit"]) /
                max(sum(1 for t in trials_data if t["hit"]), 1), 3
            ),
            "avg_efficiency": round(
                sum(t["efficiency_ratio"] for t in trials_data if t["hit"]) /
                max(sum(1 for t in trials_data if t["hit"]), 1), 3
            ),
            "total_errors": sum(t["errors"] for t in trials_data)
        },
        "trials": trials_data
    }

    filepath = export_json(session_data)

    pygame.mouse.set_visible(True)
    show_summary(screen, clock, fonts, session_data)

    pygame.quit()
    print(f"\nSesión finalizada. Datos en: {filepath}")


if __name__ == "__main__":
    main()
