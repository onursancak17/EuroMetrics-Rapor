import streamlit as st
import math
import random
from datetime import datetime, timedelta

st.set_page_config(page_title="Eurometrics Mobil", page_icon="🏭", layout="centered")

st.markdown("<h2 style='text-align: center; color: #0d47a1;'>Eurometrics Saha Asistanı</h2>", unsafe_allow_html=True)
st.divider()

metotlar = [
    "Toz EN/ISO 13284-1 (5D / 5D)", "Toz EPA 5 (2D / 8D)", "Toz EPA 5 (1.5D / 6D)",
    "Toz EPA 5 (1D / 4D)", "Toz EPA 5 (0.5D / 2D)", "Toz EPA 1 (2D / 8D)", 
    "Toz EPA 1 (1.5D / 6D)", "Toz EPA 1 (1D / 4D)", "Toz EPA 1 (0.5D / 2D)", 
    "Hız/Debi EN/ISO 16911", "Ağır Metal EN/ISO 14385 (5D / 5D)", "Ağır Metal EPA Metot 29",
    "PCDD/F Diyoksin EN/ISO 1948 (5D / 5D)", "PAH ISO 11338 (5D / 5D)", "VOC EN/ISO 13649"
]

metot = st.selectbox("Ölçüm Metodu", metotlar)

col1, col2 = st.columns(2)
with col1:
    c_seri = st.text_input("Cihaz Seri No", value="M5PMA-2310")
    tarih_str = st.text_input("Tarih (YY/AA/GG)", value="24/11/25")
    baca_no = st.text_input("Baca Adı / No", value="1")
with col2:
    saat_str = st.text_input("Başlangıç Saati (SS:DD)", value="10:00")
    sekil = st.selectbox("Baca Şekli", ["Dairesel", "Dikdörtgen"])

if sekil == "Dairesel":
    cap_cm = st.number_input("Dairesel Çap (cm)", value=45.0)
    alan_baca = math.pi * ((cap_cm/100)**2) / 4
else:
    col_k1, col_k2, col_p = st.columns(3)
    with col_k1: k1_cm = st.number_input("K1 (cm)", value=100.0)
    with col_k2: k2_cm = st.number_input("K2 (cm)", value=100.0)
    with col_p: port_sayisi_input = st.number_input("Port Sayısı", value=6, step=1)
    alan_baca = (k1_cm/100) * (k2_cm/100)
    cap_cm = (2 * k1_cm * k2_cm) / (k1_cm + k2_cm)

st.divider()
st.markdown("#### Saha Parametreleri")

c1, c2 = st.columns(2)
with c1:
    atm_mbar = st.number_input("Atmosfer Basıncı (mbar)", value=1010.5)
    bmutlak_giris_mbar = st.number_input("Baca Mutlak Basıncı (mbar)", value=1009.1)
    nem = st.number_input("Nem (%)", value=4.0)
    bsicaklik = st.number_input("Baca Sıcaklığı (°C)", value=23.5)
with c2:
    hiz = st.number_input("Baca Gazı Hızı (m/s)", value=11.0)
    nozul_mm = st.number_input("Nozul Çapı (mm)", value=6.0)
    ssicaklik = st.number_input("Sayaç Sıcaklığı (°C)", value=21.4)

st.divider()

if st.button("SAHA ŞARTLARINA GÖRE ÜRET", use_container_width=True, type="primary"):
    try:
        hedef_hiz = float(hiz)
        hedef_b_sicaklik = float(bsicaklik)
        atm_kpa = float(atm_mbar) / 10.0
        hedef_s_sicaklik = float(ssicaklik)
        
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
            else: port_sayisi = int(port_sayisi_input) 
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
        
        M_s = (28.97 * (1 - (nem/100.0))) + (18.01 * (nem/100.0)) 
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
                test_b_mut_mbar_base = float(bmutlak_giris_mbar) + random.uniform(-1.5, 1.5)
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
                    anlik_b_mut_kpa = (test_b_mut_mbar_base + random.uniform(-0.5, 0.5)) / 10.0
                    
                    hiz_farki = anlik_hiz - hedef_hiz
                    vakum_mbar = max(28, min(38, 31 + (hiz_farki * 3.0) + random.uniform(-1.0, 1.0)))
                    anlik_s_bas_kpa = (atm_mbar - vakum_mbar) / 10.0
                    anlik_izokin = random.uniform(izokin_alt, izokin_ust) 
                    
                    anlik_debi_ld = (3.14 * 60.0 * anlik_hiz * (float(nozul_mm) ** 2)) / 4000.0
                    anlik_v_act_l = anlik_debi_ld * sure_per_travers * anlik_izokin
                    anlik_v_n_nl = anlik_v_act_l * (anlik_s_bas_kpa / 101.325) * (273.15 / (273.15 + anlik_s_sic)) * ((100.0 - nem) / 100.0)
                    
                    toplam_v_act_l_temp += anlik_v_act_l
                    toplam_v_n_nl_temp += anlik_v_n_nl
                    dp_pa = ((anlik_hiz / pitot_k)**2) * (rho_std_yas * (anlik_b_mut_kpa / p_std) * (t_std / (t_std + anlik_b_sic))) / 2.0

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

        st.success("Rapor Başarıyla Üretildi! Aşağıdaki butona basarak telefonunuza indirebilirsiniz.")
        
        # SİHİRLİ İNDİRME BUTONU (Tarayıcı direkt İndirilenler klasörüne atar)
        st.download_button(
            label="📥 RAPORU İNDİR (.txt)",
            data=tum_raporlar_metni,
            file_name=f"Baca_{baca_no}_Olcum.txt",
            mime="text/plain",
            type="primary"
        )

    except Exception as e:
        st.error(f"Bir hata oluştu. Lütfen formatları kontrol edin: {e}")
