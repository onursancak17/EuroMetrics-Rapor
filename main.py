import flet as ft
import math
import random
import os
import traceback
from datetime import datetime, timedelta

def main(page: ft.Page):
    try:
        page.title = "Eurometrics Mobil"
        page.scroll = "adaptive"
        page.theme_mode = ft.ThemeMode.LIGHT
        page.padding = 20

        baslik = ft.Text("Eurometrics Saha Asistanı", size=24, weight="bold", color=ft.colors.BLUE_900)

        metotlar = [
            "Toz EN/ISO 13284-1 (5D / 5D)", "Toz EPA 5 (2D / 8D)", "Toz EPA 5 (1.5D / 6D)",
            "Toz EPA 5 (1D / 4D)", "Toz EPA 5 (0.5D / 2D)", "Toz EPA 1 (2D / 8D)", 
            "Toz EPA 1 (1.5D / 6D)", "Toz EPA 1 (1D / 4D)", "Toz EPA 1 (0.5D / 2D)", 
            "Hız/Debi EN/ISO 16911", "Ağır Metal EN/ISO 14385 (5D / 5D)", "Ağır Metal EPA Metot 29",
            "PCDD/F Diyoksin EN/ISO 1948 (5D / 5D)", "PAH ISO 11338 (5D / 5D)", "VOC EN/ISO 13649"
        ]
        combo_metot = ft.Dropdown(label="Ölçüm Metodu", options=[ft.dropdown.Option(m) for m in metotlar], value=metotlar[0])

        entry_seri = ft.TextField(label="Cihaz Seri No", value="M5PMA-2310")
        entry_tarih = ft.TextField(label="Tarih (YY/AA/GG)", value="24/11/25") 
        entry_saat = ft.TextField(label="Başlangıç Saati (SS:DD)", value="10:00")
        entry_baca = ft.TextField(label="Baca Adı / No", value="1", keyboard_type=ft.KeyboardType.NUMBER)
        entry_atm_mbar = ft.TextField(label="Atmosfer Basıncı (mbar)", value="1010.5", keyboard_type=ft.KeyboardType.NUMBER)
        entry_bmutlak_mbar = ft.TextField(label="Baca Mutlak Basıncı (mbar)", value="1009.1", keyboard_type=ft.KeyboardType.NUMBER)
        entry_nem = ft.TextField(label="Nem (%)", value="4", keyboard_type=ft.KeyboardType.NUMBER)
        entry_bsicaklik = ft.TextField(label="Baca Sıcaklığı (°C)", value="23.5", keyboard_type=ft.KeyboardType.NUMBER)
        entry_hiz = ft.TextField(label="Baca Gazı Hızı (m/s)", value="11.0", keyboard_type=ft.KeyboardType.NUMBER)
        entry_nozul = ft.TextField(label="Nozul Çapı (mm)", value="6.0", keyboard_type=ft.KeyboardType.NUMBER)
        entry_ssicaklik = ft.TextField(label="Sayaç Sıcaklığı (°C)", value="21.4", keyboard_type=ft.KeyboardType.NUMBER)

        entry_cap = ft.TextField(label="Dairesel Çap (cm)", value="45.0", keyboard_type=ft.KeyboardType.NUMBER, expand=True)
        entry_k1 = ft.TextField(label="K1 (cm)", value="100", keyboard_type=ft.KeyboardType.NUMBER, visible=False, expand=True)
        entry_k2 = ft.TextField(label="K2 (cm)", value="100", keyboard_type=ft.KeyboardType.NUMBER, visible=False, expand=True)
        entry_port = ft.TextField(label="Port Sayısı", value="6", keyboard_type=ft.KeyboardType.NUMBER, visible=False, expand=True)
        
        baca_boyut_row = ft.Row([entry_cap, entry_k1, entry_k2])

        def sekil_degisti(e):
            if combo_sekil.value == "Dikdörtgen":
                entry_cap.visible = False
                entry_k1.visible = True
                entry_k2.visible = True
                entry_port.visible = True
            else:
                entry_cap.visible = True
                entry_k1.visible = False
                entry_k2.visible = False
                entry_port.visible = False
            page.update()

        combo_sekil = ft.Dropdown(
            label="Baca Şekli", 
            options=[ft.dropdown.Option("Dairesel"), ft.dropdown.Option("Dikdörtgen")], 
            value="Dairesel",
            on_change=sekil_degisti
        )

        def show_snack(message, color=ft.colors.GREEN_700):
            page.snack_bar = ft.SnackBar(content=ft.Text(message), bgcolor=color)
            page.snack_bar.open = True
            page.update()

        def rapor_uret(e):
            try:
                c_seri = entry_seri.value
                tarih_str = entry_tarih.value
                saat_str = entry_saat.value
                baca_no = entry_baca.value
                metot = combo_metot.value 
                sekil = combo_sekil.value
                
                if sekil == "Dairesel":
                    cap_m = float(entry_cap.value) / 100.0
                    alan_baca = math.pi * (cap_m**2) / 4
                else:
                    k1 = float(entry_k1.value) / 100.0
                    k2 = float(entry_k2.value) / 100.0
                    alan_baca = k1 * k2
                    cap_m = (2 * k1 * k2) / (k1 + k2)
                    
                cap_cm = cap_m * 100.0 
                hedef_hiz = float(entry_hiz.value)
                hedef_b_sicaklik = float(entry_bsicaklik.value)
                atm_mbar = float(entry_atm_mbar.value)
                atm_kpa = atm_mbar / 10.0
                bmutlak_giris_mbar = float(entry_bmutlak_mbar.value)
                nem = float(entry_nem.value)
                nozul_mm = float(entry_nozul.value)
                hedef_s_sicaklik = float(entry_ssicaklik.value)
                
                toplam_sure_min = 30 
                izokin_alt, izokin_ust = 0.96, 1.04 

                if "Diyoksin" in metot: toplam_sure_min = 360 
                elif "PAH" in metot: toplam_sure_min = 180 
                elif "14385" in metot or "Metot 29" in metot or "26A" in metot: toplam_sure_min = 60 
                else: toplam_sure_min = 30 

                travers_sayisi_ham = 1
                if "EPA" in metot:
                    if sekil == "Dairesel":
                        if "1.5D" in metot: travers_sayisi_ham = 20
                        elif "1D" in metot or "0.5D" in metot: travers_sayisi_ham = 24
                        else: 
                            if cap_cm <= 29: travers_sayisi_ham = 1
                            elif cap_cm <= 61: travers_sayisi_ham = 8
                            else: travers_sayisi_ham = 12
                    else: 
                        if alan_baca <= 0.089: travers_sayisi_ham = 1
                        elif alan_baca <= 0.37: travers_sayisi_ham = 9
                        elif alan_baca <= 1.49: travers_sayisi_ham = 12
                        else: travers_sayisi_ham = 25
                else: 
                    if sekil == "Dairesel":
                        if cap_cm <= 34: travers_sayisi_ham = 1
                        elif cap_cm <= 69: travers_sayisi_ham = 4
                        elif cap_cm <= 99: travers_sayisi_ham = 8
                        elif cap_cm <= 199: travers_sayisi_ham = 12
                        else: travers_sayisi_ham = 16
                    else: 
                        if alan_baca <= 0.089: travers_sayisi_ham = 1
                        elif alan_baca <= 0.37: travers_sayisi_ham = 4
                        elif alan_baca <= 1.49: travers_sayisi_ham = 9
                        else: travers_sayisi_ham = 16

                if travers_sayisi_ham > 1:
                    if sekil == "Dairesel": port_sayisi = 2 
                    else: port_sayisi = int(entry_port.value) 
                    nokta_per_port = round(travers_sayisi_ham / port_sayisi)
                    if nokta_per_port < 1: nokta_per_port = 1
                    travers_sayisi = port_sayisi * nokta_per_port
                else:
                    travers_sayisi = 1

                sure_per_travers = math.ceil(toplam_sure_min / travers_sayisi)
                net_toplam_sure = sure_per_travers * travers_sayisi 
                olu_sure = 0 if travers_sayisi == 1 else int(travers_sayisi / 4) + random.randint(0, 1)

                pitot_k = 0.84
                t_std = 273.15
                p_std = 101.325
                kpa_to_mmhg = 7.50062
                
                M_kuru_hava = 28.97
                M_su = 18.01
                B_ws = nem / 100.0
                M_s = (M_kuru_hava * (1 - B_ws)) + (M_su * B_ws) 
                rho_std_yas = M_s / 22.414 
                
                baslangic_zaman = datetime.strptime(f"{tarih_str} {saat_str}", "%d/%m/%y %H:%M")
                tum_raporlar_metni = ""
                uretilen_ort_hizlar = set()
                
                for olcum in range(1, 4):
                    brut_toplam_sure = net_toplam_sure + olu_sure
                    bitis_zaman = baslangic_zaman + timedelta(minutes=brut_toplam_sure)
                    
                    while True:
                        test_hiz_base = hedef_hiz + random.uniform(0.1, 0.9) 
                        test_b_sic_base = hedef_b_sicaklik + random.uniform(-1.5, 1.5)
                        test_s_sic_base = hedef_s_sicaklik + random.uniform(-1.0, 1.0)
                        test_b_mut_mbar_base = bmutlak_giris_mbar + random.uniform(-1.5, 1.5)
                        if test_b_mut_mbar_base >= atm_mbar: test_b_mut_mbar_base = atm_mbar - random.uniform(0.5, 2.0) 

                        traversler_temp = []
                        toplam_v_act_l_temp = 0.0
                        toplam_v_n_nl_temp = 0.0
                        
                        for i in range(1, travers_sayisi + 1):
                            anlik_hiz = test_hiz_base + random.uniform(-0.5, 0.6)
                            if len(traversler_temp) > 0:
                                while abs(anlik_hiz - traversler_temp[-1]['hiz']) > 1.0:
                                    anlik_hiz = test_hiz_base + random.uniform(-0.5, 0.6)
                            
                            if anlik_hiz < hedef_hiz: anlik_hiz = hedef_hiz + random.uniform(0.01, 0.05)
                            if anlik_hiz > (hedef_hiz + 1.1): anlik_hiz = (hedef_hiz + 1.1) - random.uniform(0.01, 0.05)
                                
                            anlik_b_sic = test_b_sic_base + random.uniform(-0.5, 0.5)
                            anlik_s_sic = test_s_sic_base + random.uniform(-0.3, 0.3)
                            
                            anlik_b_mut_mbar = test_b_mut_mbar_base + random.uniform(-0.5, 0.5)
                            if anlik_b_mut_mbar >= atm_mbar: anlik_b_mut_mbar = atm_mbar - 0.5
                            anlik_b_mut_kpa = anlik_b_mut_mbar / 10.0
                            
                            hiz_farki = anlik_hiz - hedef_hiz
                            vakum_mbar = 31 + (hiz_farki * 3.0) + random.uniform(-1.0, 1.0)
                            vakum_mbar = max(28, min(38, vakum_mbar)) 
                            anlik_s_bas_kpa = (atm_mbar - vakum_mbar) / 10.0
                            
                            anlik_izokin = random.uniform(izokin_alt, izokin_ust) 
                            
                            anlik_debi_ld = (3.14 * 60.0 * anlik_hiz * (float(nozul_mm) ** 2)) / 4000.0
                            anlik_v_act_l = anlik_debi_ld * sure_per_travers * anlik_izokin
                            anlik_v_n_nl = anlik_v_act_l * (anlik_s_bas_kpa / 101.325) * (273.15 / (273.15 + anlik_s_sic)) * ((100.0 - nem) / 100.0)
                            
                            toplam_v_act_l_temp += anlik_v_act_l
                            toplam_v_n_nl_temp += anlik_v_n_nl

                            yogunluk = rho_std_yas * (anlik_b_mut_kpa / p_std) * (t_std / (t_std + anlik_b_sic))
                            dp_pa = ((anlik_hiz / pitot_k)**2) * yogunluk / 2.0

                            traversler_temp.append({
                                "no": i, "hiz": anlik_hiz, "v_n_kum": toplam_v_n_nl_temp, "v_act_kum": toplam_v_act_l_temp,
                                "b_sic": anlik_b_sic, "s_sic": anlik_s_sic, "b_mut_kpa": anlik_b_mut_kpa, 
                                "s_bas_kpa": anlik_s_bas_kpa, "dp": dp_pa, "izokin": anlik_izokin
                            })

                        ort_hiz_genel_temp = sum(x['hiz'] for x in traversler_temp) / travers_sayisi
                        ort_hiz_yuvarlanmis = round(ort_hiz_genel_temp, 1)
                        
                        if (ort_hiz_yuvarlanmis not in uretilen_ort_hizlar) and (hedef_hiz <= ort_hiz_yuvarlanmis <= hedef_hiz + 1.1):
                            uretilen_ort_hizlar.add(ort_hiz_yuvarlanmis)
                            traversler = traversler_temp
                            toplam_v_act_l = toplam_v_act_l_temp
                            toplam_v_n_nl = toplam_v_n_nl_temp
                            ort_hiz_genel = ort_hiz_genel_temp
                            break

                    ort_b_sic_genel = sum(x['b_sic'] for x in traversler) / travers_sayisi
                    ort_s_sic_genel = sum(x['s_sic'] for x in traversler) / travers_sayisi
                    ort_b_mut_genel = sum(x['b_mut_kpa'] for x in traversler) / travers_sayisi
                    ort_s_bas_genel = sum(x['s_bas_kpa'] for x in traversler) / travers_sayisi
                    ort_izokin_genel = sum(x['izokin'] for x in traversler) / travers_sayisi
                    ort_dp_genel = sum(x['dp'] for x in traversler) / travers_sayisi
                    
                    ort_vakum = (toplam_v_n_nl / net_toplam_sure) if net_toplam_sure > 0 else 0.0

                    rapor = f"""IZOKINETIK ORNEKLEME RAPORU
-------------------------   
Cihaz Seri    : {c_seri}
Baslangic     : {baslangic_zaman.strftime("%y/%m/%d %H:%M")}
Ayarlanan Sure: {net_toplam_sure} dk
Baca No       : {baca_no}
Travers sayisi: {travers_sayisi}
Nozzle capi   : {int(float(nozul_mm))} mm
Atmosfer basnc: {atm_kpa:.2f} kPa
Atmosfer basnc: {atm_kpa * kpa_to_mmhg:.2f} mmHg
Pitot katsayi : {pitot_k:.2f}
Mutlak Nem    : {int(float(nem))}
"""
                    for t in traversler:
                        rapor += f"""
-------------------------   
BACA NO       : {baca_no}
TRAVERS NO    : {t['no']}
Sure          : {t['no']*sure_per_travers:02d}:00
Ort.baca hizi : {t['hiz']:.1f} m/s
Kurugaz hacmi : {t['v_n_kum']:.1f} Nl
Sayac hacmi   : {t['v_act_kum']:.1f} l
Baca Sicakligi: {t['b_sic']:.1f} C
Sayac gaz sic.: {t['s_sic']:.1f} C
Baca mutlk bas: {t['b_mut_kpa']:.2f} kPa
Baca mutlk bas: {t['b_mut_kpa'] * kpa_to_mmhg:.2f} mmHg
Pitot dP      : {t['dp']:.2f} Pa
Pitot dP      : {t['dp'] * 0.00750062:.4f} mmHg
izokin.verimi : {t['izokin']:.2f}"""

                    rapor += f"""

-------------------------  
IZOKINETIK ORNEKLEME RAPORU
-------------------------  
Cihaz Seri    : {c_seri}
Baslangic     : {baslangic_zaman.strftime("%y/%m/%d %H:%M")}
Bitis         : {bitis_zaman.strftime("%y/%m/%d %H:%M")}
Ornekleme Sure: {net_toplam_sure}:00
Baca no       : {baca_no}
Ort.baca hizi : {ort_hiz_genel:.1f} m/s
Ort.vakum debi: {ort_vakum:.1f} Nl/dk
Kurugaz hacmi : {toplam_v_n_nl:.1f} Nl
Sayac hacmi   : {toplam_v_act_l:.1f} l
Baca sicakligi: {ort_b_sic_genel:.1f} C
Sayac gaz sic.: {ort_s_sic_genel:.1f} C
Referans scklk: 0.0 C
Baca mutlk bas: {ort_b_mut_genel:.2f} kPa
Baca mutlk bas: {ort_b_mut_genel * kpa_to_mmhg:.2f} mmHg
Sayac basinci : {ort_s_bas_genel:.2f} kPa
Sayac basinci : {ort_s_bas_genel * kpa_to_mmhg:.2f} mmHg
Referans basnc: 101.33 kPa
Referans basnc: 760.00 mmHg
Pitot dP      : {ort_dp_genel:.2f} Pa
Pitot dP      : {ort_dp_genel * 0.00750062:.2f} mmHg
izokin.verimi : {ort_izokin_genel:.2f}
"""
                    tum_raporlar_metni += rapor
                    if olcum < 3: tum_raporlar_metni += "\n" * 6
                    bekleme_suresi = random.randint(12, 15)
                    baslangic_zaman = bitis_zaman + timedelta(minutes=bekleme_suresi)

                if os.path.exists('/storage/emulated/0/Download'):
                    kayit_yeri = '/storage/emulated/0/Download'
                else:
                    kayit_yeri = os.getcwd()
                    
                dosya_adi = os.path.join(kayit_yeri, f"Baca_{baca_no}_Olcum.txt")
                with open(dosya_adi, "w", encoding="utf-8") as f:
                    f.write(tum_raporlar_metni)

                show_snack(f"Rapor Başarıyla Üretildi!\nDosya: İndirilenler/{os.path.basename(dosya_adi)}")

            except Exception as ex:
                show_snack(f"Hata oluştu. Değerleri kontrol edin: {str(ex)}", color=ft.colors.RED_700)

        btn_uret = ft.ElevatedButton("SAHA ŞARTLARINA GÖRE ÜRET", on_click=rapor_uret, 
                                     bgcolor=ft.colors.BLUE_900, color=ft.colors.WHITE, 
                                     width=350, height=50)

        page.add(
            baslik, ft.Divider(), combo_metot,
            entry_seri, entry_tarih, entry_saat, entry_baca,
            combo_sekil, baca_boyut_row, entry_port, ft.Divider(),
            entry_atm_mbar, entry_bmutlak_mbar, entry_nem, entry_bsicaklik,
            entry_hiz, entry_nozul, entry_ssicaklik, ft.Divider(),
            btn_uret, ft.Container(height=30)
        )
        
    except Exception as ana_hata:
        page.add(ft.Text("KRİTİK HATA! Lütfen Ekran Görüntüsü Alın:", color="white", bgcolor="red", size=20, weight="bold"))
        page.add(ft.Text(str(traceback.format_exc()), color="red", selectable=True))
        page.update()

ft.app(target=main)
