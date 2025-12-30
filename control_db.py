from __init__ import db
from sqlalchemy import text

def create_procedure():
    db.session.execute(text("DROP PROCEDURE IF EXISTS ThemLichKham"))
    db.session.commit()

    sql = """
        CREATE PROCEDURE ThemLichKham(
            IN p_MaNhaSi INT,
            IN p_NgayKham DATE,
            IN p_GioKham TIME,
            IN p_MaKhachHang INT,
            IN p_MaDichVu INT
        )
        BEGIN
            DECLARE lich_count INT;
        
            -- Kiểm tra trùng giờ
            SELECT COUNT(*) INTO lich_count
            FROM LichKham
            WHERE NhaSiId = p_MaNhaSi
              AND NgayKham = p_NgayKham
              AND GioKham = p_GioKham;
        
            IF lich_count > 0 THEN
                SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nha sĩ đã có hẹn vào giờ này';
            ELSE
                -- Kiểm tra tổng số lịch trong ngày
                SELECT COUNT(*) INTO lich_count
                FROM LichKham
                WHERE NhaSiId = p_MaNhaSi
                  AND NgayKham = p_NgayKham;
        
                IF lich_count >= 5 THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Nha sĩ đã đủ 5 lịch khám trong ngày';
                ELSE
                    INSERT INTO LichKham(NhaSiId, KhachHangId, DichVuId, NgayKham, GioKham, created_date, active)
                    VALUES (p_MaNhaSi, p_MaKhachHang, p_MaDichVu, p_NgayKham, p_GioKham, NOW(), 1);
                END IF;
            END IF;
        END;
        """
    db.session.execute(text(sql))
    db.session.commit()
