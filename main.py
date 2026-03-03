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
    dosya_adi_input = st.text_input("Kayıt Edilecek Dosya Adı", value="Baca_1_Olcum")

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
    nem = st.number_input("Nem (%)", value=4.0)
    bsicaklik = st.number_input("Baca Sıcaklığı (°C)", value=23.5)
with c2:
    hiz_input = st.number_input("Hedef Baca Gazı Hızı (m/s)", value=11.5)
    nozul_mm = st.number_input("Nozul Çapı (mm)", value=6.0)
    ssicaklik = st.number_input("Sayaç Sıcaklığı (°C)", value=21.4)

st.divider()

if st.button("SAHA ŞARTLARINA GÖRE ÜRET", use_container_width=True, type="primary"):
    try:
        hedef_hiz_ana = float(hiz_input)
        hedef_b_sicaklik = float(bsicaklik)
        atm_kpa = float(atm_mbar) / 10.0
        hedef_s_sicaklik = float(ssicaklik)
        
        # Süre hesapları
        toplam_sure_min = 30 
        if "Diyoksin" in metot: toplam_sure_min = 360 
        elif "PAH" in metot: toplam_sure_min = 180 
        elif any(x in metot for x in ["14385", "Metot 29", "26A"]): toplam_sure_min = 60 

        # Travers nokta hesapları
        if sekil == "Dairesel":
            if cap_cm <= 34: t_ham = 1
            elif cap_cm <= 69: t_ham = 4
            elif cap_cm <= 99: t_ham = 8
            elif cap_cm <= 199: t_ham = 12
            else: t_ham = 16
        else:
            if alan_baca <= 0.089: t_ham = 1
            elif alan_baca <= 0.37: t_ham = 4
            elif alan_baca <= 1.49: t_ham = 9
            else: t_ham = 16
        
        travers_sayisi = t_ham
        sure_per_travers = math.ceil(toplam_sure_min / travers_sayisi)
        net_toplam_sure = sure_per_travers * travers_sayisi 
        olu_sure = 0 if travers_sayisi == 1 else int(travers_sayisi / 4) + random.randint(0, 1)

        pitot_k = 0.84
        p_std = 101.325
        t_std = 273.15
        kpa_to_mmhg = 7.50062
        M_s = (28.97 * (1 - (nem/100.0))) + (18.01 * (nem/100.0)) 
        rho_std_yas = M_s / 22.414 
        
        baslangic_zaman = datetime.strptime(f"{tarih_str} {saat_str}", "%d/%m/%y %H:%M")
        tum_raporlar_metni = ""
        
        # 3 ARDIŞIK ÖLÇÜM DÖNGÜSÜ
        for olcum in range(1, 4):
            # GERÇEKÇİ HIZ DALGALANMASI
            if olcum == 1: 
                current_hiz_base = hedef_hiz_ana + random.uniform(-0.1, 0.1)
            elif olcum == 2: 
                current_hiz_base = hedef_hiz_ana - random.uniform(0.3, 0.4)
            else: 
                current_hiz_base = hedef_hiz_ana + random.uniform(0.3, 0.4)
            
            # MUTLAK BASINÇ DALGALANMASI (-0.7 ile +0.7 ARASI HASSAS AYAR)
            sapma_mbar = random.uniform(-0.7, 0.7)
            hedef_b_mut_mbar_test = (float(atm_mbar) - 1.2) + sapma_mbar
            
            bitis_zaman = baslangic_zaman + timedelta(minutes=(net_toplam_sure + olu_sure))

            traversler = []
            toplam_v_act_l = 0.0
            toplam_v_n_nl = 0.0
            
            for i in range(1, travers_sayisi + 1):
                # O anki testin hız merkezinde ufak dalgalanmalar
                anlik_hiz = current_hiz_base + random.uniform(-0.3, 0.3)
                anlik_b_sic = hedef_b_sicaklik + random.uniform(-0.8, 0.8)
                anlik_s_sic = hedef_s_sicaklik + random.uniform(-0.4, 0.4)
                
                # Dinamik mutlak basınç (O testin merkezine göre türbülans)
                anlik_b_mut_mbar = hedef_b_mut_mbar_test + random.uniform(-0.15, 0.15)
                anlik_b_mut_kpa = anlik_b_mut_mbar / 10.0
                
                # Sayaç Vakumu ve Filtre şişmesi (Hıza bağlı olarak pompa daha çok zorlanır)
                filtre_etkisi = (i / travers_sayisi) * (anlik_hiz * 0.25)
                vakum = 26.0 + (anlik_hiz * 0.45) + filtre_etkisi + random.uniform(-0.5, 0.5)
                anlik_s_bas_kpa = (float(atm_mbar) - vakum) / 10.0
                
                anlik_izokin = random.uniform(0.97, 1.03)
                anlik_debi_ld = (3.14 * 60.0 * anlik_hiz * (float(nozul_mm) ** 2)) / 4000.0
                anlik_v_act_l = anlik_debi_ld * sure_per_travers * anlik_izokin
                anlik_v_n_nl = anlik_v_act_l * (anlik_s_bas_kpa / p_std) * (t_std / (t_std + anlik_s_sic)) * ((100.0 - nem) / 100.0)
                
                toplam_v_act_l += anlik_v_act_l
                toplam_v_n_nl += anlik_v_n_nl
                
                yogunluk = rho_std_yas * (atm_kpa / p_std) * (t_std / (t_std + anlik_b_sic))
                dp_pa = ((anlik_hiz / pitot_k)**2) * yogunluk / 2.0

                traversler.append({
                    "no": i, "hiz": anlik_hiz, "v_n_kum": toplam_v_n_nl, "v_act_kum": toplam_v_act_l,
                    "b_sic": anlik_b_sic, "s_sic": anlik_s_sic, "b_mut_kpa": anlik_b_mut_kpa, 
                    "s_bas_kpa": anlik_s_bas_kpa, "dp": dp_pa, "izokin": anlik_izokin
                })

            # 3. Özet değerler
            o_hiz = sum(x['hiz'] for x in traversler) / travers_sayisi
            o_b_sic = sum(x['b_sic'] for x in traversler) / travers_sayisi
            o_s_sic = sum(x['s_sic'] for x in traversler) / travers_sayisi
            o_b_mut = sum(x['b_mut_kpa'] for x in traversler) / travers_sayisi
            o_s_bas = sum(x['s_bas_kpa'] for x in traversler) / travers_sayisi
            o_izokin = sum(x['izokin'] for x in traversler) / travers_sayisi
            o_dp = sum(x['dp'] for x in traversler) / travers_sayisi
            o_vakum_debi = (toplam_v_n_nl / net_toplam_sure)

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
Ort.baca hizi : {o_hiz:.1f} m/s
Ort.vakum debi: {o_vakum_debi:.1f} Nl/dk
Kurugaz hacmi : {toplam_v_n_nl:.1f} Nl
Sayac hacmi   : {toplam_v_act_l:.1f} l
Baca sicakligi: {o_b_sic:.1f} C
Sayac gaz sic.: {o_s_sic:.1f} C
Referans scklk: 0.0 C
Baca mutlk bas: {o_b_mut:.2f} kPa
Baca mutlk bas: {o_b_mut * kpa_to_mmhg:.2f} mmHg
Sayac basinci : {o_s_bas:.2f} kPa
Sayac basinci : {o_s_bas * kpa_to_mmhg:.2f} mmHg
Referans basnc: 101.33 kPa
Referans basnc: 760.00 mmHg
Pitot dP      : {o_dp:.2f} Pa
Pitot dP      : {o_dp * 0.00750062:.2f} mmHg
izokin.verimi : {o_izokin:.2f}
"""
            tum_raporlar_metni += rapor
            if olcum < 3: tum_raporlar_metni += "\n" * 6
            baslangic_zaman = bitis_zaman + timedelta(minutes=random.randint(12, 15))

        st.success("Saha Simülasyonu Başarıyla Tamamlandı!")
        st.download_button(
            label="📥 GERÇEKÇİ RAPORU İNDİR (.txt)",
            data=tum_raporlar_metni,
            file_name=f"{dosya_adi_input}.txt",
            mime="text/plain",
            type="primary"
        )

    except Exception as e:
        st.error(f"Saha verilerinde hata: {e}")
