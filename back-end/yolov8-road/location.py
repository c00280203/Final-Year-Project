import webbrowser
import exifread
import os


def get_gps_coordinates(image_path):
    """
    从图片中提取GPS坐标信息
    """
    with open(image_path, 'rb') as f:
        tags = exifread.process_file(f)

    if not tags:
        print("无法读取图片的EXIF信息")
        return None

    # 提取GPS信息
    gps_latitude = tags.get('GPS GPSLatitude')
    gps_latitude_ref = tags.get('GPS GPSLatitudeRef')
    gps_longitude = tags.get('GPS GPSLongitude')
    gps_longitude_ref = tags.get('GPS GPSLongitudeRef')

    if not all([gps_latitude, gps_latitude_ref, gps_longitude, gps_longitude_ref]):
        print("图片中未找到GPS坐标信息")
        return None

    # 将度分秒格式转换为十进制
    def convert_to_decimal(gps_value, ref):
        # 度分秒格式: [(度, 分, 秒), ...]
        degrees = gps_value.values[0].num / gps_value.values[0].den
        minutes = gps_value.values[1].num / gps_value.values[1].den
        seconds = gps_value.values[2].num / gps_value.values[2].den

        decimal = degrees + minutes / 60 + seconds / 3600

        # 根据参考方向调整正负
        if ref in ['S', 'W']:
            decimal = -decimal

        return decimal

    lat = convert_to_decimal(gps_latitude, gps_latitude_ref.values)
    lon = convert_to_decimal(gps_longitude, gps_longitude_ref.values)

    return lat, lon


def open_in_google_maps(lat, lon):
    """
    在Google Maps中打开位置
    """
    url = f"https://www.google.com/maps?q={lat},{lon}"
    webbrowser.open(url)
    print(f"在Google Maps中打开位置: {lat}, {lon}")


def open_in_apple_maps(lat, lon):
    """
    在Apple Maps中打开位置
    """
    url = f"https://maps.apple.com/?q={lat},{lon}"
    webbrowser.open(url)
    print(f"在Apple Maps中打开位置: {lat}, {lon}")


def main():
    # 图片路径
    image_path = input("请输入图片路径: ").strip().strip('"')

    if not os.path.exists(image_path):
        print("图片文件不存在")
        return

    # 获取GPS坐标
    coordinates = get_gps_coordinates(image_path)

    if coordinates:
        lat, lon = coordinates

        print(f"\n提取到的GPS坐标:")
        print(f"纬度: {lat}")
        print(f"经度: {lon}")

        # 选择地图服务
        print("\n选择地图服务:")
        print("1. Google Maps")
        print("2. Apple Maps")
        print("3. 两者都打开")

        choice = input("请输入选择 (1/2/3): ").strip()

        if choice == '1':
            open_in_google_maps(lat, lon)
        elif choice == '2':
            open_in_apple_maps(lat, lon)
        elif choice == '3':
            open_in_google_maps(lat, lon)
            open_in_apple_maps(lat, lon)
        else:
            print("无效选择")
    else:
        print("无法从图片中提取GPS信息")


if __name__ == "__main__":
    main()