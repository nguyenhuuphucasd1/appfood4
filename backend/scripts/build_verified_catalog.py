"""Build the reviewed, original Vietnamese recipe catalog for the remaining 30 dishes."""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
OUTPUT = PROJECT_DIR / "backend" / "data" / "recipes" / "verified_recipes.vi.json"
LIST_REFERENCE = "https://en.wikipedia.org/wiki/List_of_Vietnamese_dishes"
ACCESSED_AT = "2026-10-24"


# Timing/yield values are copied from the referenced recipe metadata.  The
# catalog-only ``metadataSourceUrl`` lets the importer prove that the source
# used for these values is also present in ``references`` without changing the
# database or public API.
RECIPE_METADATA = {
    "banh-beo": (40, 25, 65, 4, "4 phần", "https://vietnamesecookbook.com/recipes/banh-beo-chen/"),
    "banh-bot-loc": (60, 30, 90, 6, "6 phần", "https://vietnamesecookbook.com/recipes/banh-bot-loc/"),
    "banh-canh": (40, 40, 80, 4, "4 phần", "https://vietnamesecookbook.com/recipes/banh-canh-cha-ca/"),
    "banh-cu-do": (20, 30, 80, None, "8–10 miếng", "https://eggyolk.vn/cach-lam-keo-cu-do-bang-duong-deo-thom-chuan-vi-ha-tinh/"),
    "banh-cuon": (40, 45, 85, 4, "4 phần", "https://vietnamesecookbook.com/recipes/banh-cuon/"),
    "banh-can": (30, 30, 60, 4, "4 phần", "https://vietnamesecookbook.com/recipes/banh-can/"),
    "banh-gio": (60, 40, 160, None, "14 bánh (6–8 phần)", "https://helenrecipes.com/recipe-52-banh-gio-vietnamese-rice-pyramid-dumplings/"),
    "banh-khot": (25, 5, 50, 4, "4 phần", "https://www.kitchentomytable.com/view_recipe_data.php?id=10080"),
    "banh-mi-cay": (30, 30, 60, 6, "6 phần", "https://vietnamesecookbook.com/recipes/banh-mi-cay/"),
    "banh-pia": (120, 45, 165, None, "12 bánh", "https://chefmundo.com/cong-thuc/banh-ngot/banh-pia/"),
    "banh-trang-nuong": (15, 20, 35, 6, "6 phần", "https://vietnamesecookbook.com/recipes/banh-trang-nuong/"),
    "banh-tet": (180, 600, 780, None, "4–5 đòn (10–15 phần)", "https://helenrecipes.com/vi/recipe-banh-tet-vietnamese-cylindrical-sticky-rice-cake-2/"),
    "banh-xeo": (30, 40, 70, 4, "4 phần", "https://vietnamesecookbook.com/recipes/banh-xeo/"),
    "banh-da-cua": (45, 90, 135, 6, "6 phần", "https://vietnamesecookbook.com/recipes/banh-da-cua/"),
    "banh-duc": (30, 45, 75, 4, "4 phần", "https://vietnamesecookbook.com/recipes/banh-duc-tau/"),
    "banh-dau-xanh": (30, 120, 150, 4, "4 phần", "https://www.dienmayxanh.com/vao-bep/2-cach-lam-banh-dau-xanh-trai-cay-va-nuong-thom-ngon-don-01944"),
    "bun-ca": (30, 60, 90, 4, "4 phần", "https://vietnamesecookbook.com/recipes/bun-ca-cay/"),
    "bun-mam": (35, 60, 95, 4, "4 phần", "https://vietnamesecookbook.com/recipes/bun-mam/"),
    "bun-rieu": (40, 50, 90, 4, "4 phần", "https://vietnamesecookbook.com/recipes/bun-rieu/"),
    "bun-thit-nuong": (30, 30, 180, 4, "4 phần", "https://joyofcooking.com/recipes/bun-thit-nuong/"),
    "bun-dau-mam-tom": (25, 20, 45, 2, "2 phần", "https://vietnamesecookbook.com/recipes/bun-dau-mam-tom/"),
    "chao-long": (45, 90, 135, 6, "6 phần", "https://world.food/recipes/vietnam/chao-long"),
    "ca-kho-to": (15, 45, 60, 4, "4 phần", "https://vietnamesecookbook.com/recipes/ca-kho-to/"),
    "com-chay": (35, 80, 205, 4, "4 phần", "https://travelshelper.com/world-of-food/vietnamese-national-dishes/c%C6%A1m-ch%C3%A1y-ninh-b%C3%ACnh-crispy-rice-cakes-with-goat-sauce/"),
    "com-tam": (25, 35, 60, 4, "4 phần", "https://vietnamesecookbook.com/recipes/com-tam/"),
    "hu-tieu": (40, 180, 220, 6, "6 phần", "https://vietnamesecookbook.com/recipes/hu-tieu/"),
    "mi-quang": (40, 45, 85, 4, "4 phần", "https://vietnamesecookbook.com/recipes/mi-quang/"),
    "nem-chua": (90, 0, 4320, None, "20 cuốn", "https://world.food/recipes/vietnam/nem-chua"),
    "nem-nuong": (45, 15, 60, 4, "4 phần", "https://vietnamesecookbook.com/recipes/nem-nuong-nha-trang/"),
    "xoi-xeo": (20, 50, 70, 4, "4 phần", "https://vietnamesecookbook.com/recipes/xoi-xeo/"),
}

EXTRA_METADATA_REFERENCES = {
    "banh-cu-do": [
        {
            "name": "Cu đơ – thức quà tâm tình của người Hà Tĩnh",
            "url": "https://vntravellive.com/cu-do--thuc-qua-tam-tinh-cua-nguoi-ha-tinh-d35616.html",
            "publisher": "Vietnam Travel Live",
            "accessedAt": ACCESSED_AT,
        }
    ]
}


def dish(
    slug: str,
    name: str,
    description: str,
    image: str,
    primary_url: str,
    ingredients: str,
    steps: list[str],
    *,
    region: str | None = None,
    category: str = "Món chính",
    primary_name: str = "Vietnamese Cookbook",
    primary_publisher: str = "Vietnamese Cookbook",
) -> dict:
    prep, cook, total, servings, servings_text, metadata_source_url = RECIPE_METADATA[slug]
    references = [
        {
            "name": primary_name,
            "url": primary_url,
            "publisher": primary_publisher,
            "accessedAt": ACCESSED_AT,
        },
        {
            "name": "List of Vietnamese dishes",
            "url": LIST_REFERENCE,
            "publisher": "Wikipedia contributors",
            "accessedAt": ACCESSED_AT,
        },
    ]
    if metadata_source_url not in {item["url"] for item in references}:
        references.append(
            {
                "name": "Nguồn thời gian và khẩu phần",
                "url": metadata_source_url,
                "publisher": metadata_source_url.split("/")[2],
                "accessedAt": ACCESSED_AT,
            }
        )
    references.extend(EXTRA_METADATA_REFERENCES.get(slug, []))
    return {
        "slug": slug,
        "name": name,
        "aliases": [name.replace("đ", "d").replace("Đ", "D")],
        "region": region,
        "category": category,
        "prepMinutes": prep,
        "cookMinutes": cook,
        "totalMinutes": total,
        "difficulty": None,
        "servings": servings,
        "servingsText": servings_text,
        "metadataSourceUrl": metadata_source_url,
        "description": description,
        "commonsFileTitle": image,
        "sourceName": "Vị Việt",
        "sourceUrl": primary_url,
        "sourceRevisionUrl": primary_url,
        "sourceLicenseName": "CC BY-SA 4.0",
        "sourceLicenseUrl": "https://creativecommons.org/licenses/by-sa/4.0/",
        "sourceAttribution": (
            "Vị Việt biên soạn mới bằng tiếng Việt và đối chiếu các nguồn tham khảo; "
            "không sao chép nguyên văn và không tuyên bố đã được chuyên gia kiểm duyệt."
        ),
        "sourceModified": False,
        "contentOrigin": "original_synthesis",
        "verificationStatus": "cross_checked",
        "verificationNote": "Vị Việt biên soạn và đối chiếu nguồn; chưa được chuyên gia kiểm duyệt.",
        "references": references,
        "ingredients": [{"name": item.strip()} for item in ingredients.split(";")],
        "steps": steps,
    }


DISHES = [
    dish(
        "banh-beo", "Bánh bèo",
        "Phiên bản bánh bèo chén miền Trung, bánh mềm mỏng, phủ tôm cháy, mỡ hành và dùng cùng nước mắm pha.",
        "File:Bánh bèo chén.jpg", "https://vietnamesecookbook.com/recipes/banh-beo-chen/",
        "Bột gạo;Bột năng;Nước;Tôm;Hành lá;Dầu ăn;Nước mắm;Đường;Ớt",
        ["Hòa bột gạo và bột năng với nước, để bột nghỉ rồi khuấy lại cho đồng nhất.", "Quét một lớp dầu mỏng vào chén nhỏ và làm nóng chén trong xửng hấp.", "Rót lớp bột vừa phải vào từng chén, hấp đến khi bánh trong và se mặt.", "Làm tôm cháy từ tôm chín giã nhỏ; phi mỡ hành riêng.", "Phủ tôm cháy và mỡ hành lên bánh, dùng nóng với nước mắm chua ngọt."],
        region="Miền Trung", category="Bánh mặn",
    ),
    dish(
        "banh-bot-loc", "Bánh bột lọc",
        "Bánh bột lọc Huế có vỏ bột năng trong, nhân tôm thịt đậm vị và được gói lá chuối trước khi hấp.",
        "File:Bánh bột lọc.jpg", "https://vietnamesecookbook.com/recipes/banh-bot-loc/",
        "Bột năng;Nước sôi;Tôm nhỏ;Thịt ba chỉ;Hành tím;Nước mắm;Đường;Tiêu;Lá chuối",
        ["Xào săn thịt ba chỉ và tôm với hành tím, nước mắm, đường và tiêu; để nguội.", "Châm nước sôi vào bột năng từng ít một, trộn rồi nhồi đến khi khối bột dẻo mịn.", "Chia bột, cán mỏng, đặt nhân tôm thịt vào giữa và miết kín mép.", "Đặt bánh vào lá chuối đã làm mềm, gói kín rồi xếp vào xửng.", "Hấp đến khi vỏ bánh trong, dùng với mỡ hành và nước mắm pha."],
        region="Huế", category="Bánh mặn",
    ),
    dish(
        "banh-canh", "Bánh canh",
        "Bánh canh chả cá theo phong cách miền Trung, dùng sợi dày trong nước dùng cá thanh và chả cá dai.",
        "File:Banh-Canh-Noodle-Soup.jpg", "https://vietnamesecookbook.com/recipes/banh-canh-cha-ca/",
        "Sợi bánh canh;Cá làm nước dùng;Chả cá;Hành tím;Hành lá;Rau mùi;Nước mắm;Tiêu",
        ["Làm sạch cá, nấu cùng hành tím để lấy nước dùng rồi lọc bỏ xương.", "Nêm nước dùng bằng nước mắm và gia vị vừa ăn, giữ sôi nhẹ.", "Chiên hoặc hấp chả cá rồi cắt miếng vừa ăn.", "Trụng sợi bánh canh đến độ mềm mong muốn và chia vào tô.", "Chan nước dùng, thêm chả cá, hành lá, rau mùi và tiêu."],
        region="Miền Trung", category="Món nước",
    ),
    dish(
        "banh-cu-do", "Bánh cu đơ",
        "Kẹo lạc Hà Tĩnh kẹp bánh tráng, có vị mật mía, gừng và lạc rang giòn.",
        "File:KeoCudo.JPG", "https://trangiafoods.vn/blogs/news/cach-lam-banh-cu-do-ha-tinh/",
        "Lạc nhân;Mật mía;Mạch nha;Gừng tươi;Bánh tráng mè",
        ["Rang lạc chín thơm, xát bớt vỏ lụa và giữ hạt nguyên.", "Đun mật mía với mạch nha trên lửa vừa, khuấy đều để hỗn hợp không bén nồi.", "Thêm gừng thái sợi khi mật đạt độ sánh và tiếp tục đảo ngắn.", "Cho lạc rang vào, trộn nhanh để mật áo đều từng hạt.", "Múc hỗn hợp lên bánh tráng, ép một miếng bánh khác lên trên và để nguội hẳn."],
        region="Hà Tĩnh", category="Bánh ngọt", primary_name="Cách làm bánh cu đơ Hà Tĩnh", primary_publisher="Trần Gia Foods",
    ),
    dish(
        "banh-cuon", "Bánh cuốn",
        "Bánh cuốn nhân thịt là lớp bột gạo hấp mỏng cuộn thịt băm và mộc nhĩ, ăn cùng hành phi và nước chấm.",
        "File:Bánh cuốn chả lụa.jpg", "https://vietnamesecookbook.com/recipes/banh-cuon/",
        "Bột gạo;Bột năng;Nước;Thịt heo băm;Mộc nhĩ;Hành tím;Hành phi;Nước mắm;Rau thơm",
        ["Ngâm nở mộc nhĩ rồi băm nhỏ; xào cùng thịt và hành tím đến chín, nêm vừa ăn.", "Pha bột gạo, bột năng và nước thành hỗn hợp loãng, để bột nghỉ.", "Tráng một lớp bột thật mỏng trên mặt nồi hấp, đậy nắp đến khi bánh trong.", "Lấy bánh ra mặt phẳng sạch, đặt nhân và cuộn nhẹ tay.", "Rắc hành phi, dùng với rau thơm, chả lụa tùy chọn và nước mắm pha."],
        region="Miền Bắc", category="Bánh mặn",
    ),
    dish(
        "banh-can", "Bánh căn",
        "Bánh căn miền Trung được đổ trong khuôn đất, mặt bánh mềm xốp, thường có trứng hoặc hải sản và ăn với nước chấm.",
        "File:Bánh căn in phan rang, vietnam.jpg", "https://vietnamesecookbook.com/recipes/banh-can/",
        "Bột gạo;Nước;Trứng cút;Tôm;Mực;Hành lá;Dầu ăn;Nước mắm;Rau sống",
        ["Pha bột gạo với nước thành hỗn hợp sánh vừa và để bột nghỉ.", "Làm nóng khuôn bánh căn, quét rất ít dầu vào từng lỗ khuôn.", "Rót bột, thêm trứng cút hoặc hải sản đã sơ chế lên mặt.", "Đậy nắp đến khi viền bánh se lại và mặt bánh chín.", "Gỡ bánh khỏi khuôn, thêm mỡ hành và dùng ngay với nước chấm cùng rau sống."],
        region="Nam Trung Bộ", category="Bánh mặn",
    ),
    dish(
        "banh-gio", "Bánh giò",
        "Bánh giò miền Bắc có lớp bột gạo mềm, nhân thịt băm mộc nhĩ và dáng chóp gói lá chuối.",
        "File:Bánh giò.jpg", "https://www.vietworldkitchen.com/blog/2018/05/vietnamese-rice-and-pork-pyramid-dumplings-recipe-banh-gio.html",
        "Bột gạo;Bột bắp;Nước dùng gà;Thịt heo băm;Mộc nhĩ;Hành tím;Nước mắm;Lá chuối",
        ["Xào hành tím, thịt băm và mộc nhĩ; nêm nước mắm, tiêu rồi để nhân nguội.", "Hòa bột gạo và bột bắp với nước dùng, lọc để hỗn hợp mịn.", "Khuấy bột trên lửa vừa đến khi đặc dẻo nhưng chưa chín hoàn toàn.", "Gấp lá chuối thành khuôn chóp, cho bột, nhân rồi phủ thêm bột và gói kín.", "Hấp bánh đến khi bột chín mềm, để nghỉ vài phút trước khi mở lá."],
        region="Miền Bắc", category="Bánh mặn", primary_name="Vietnamese Rice and Pork Pyramid Dumplings", primary_publisher="Viet World Kitchen",
    ),
    dish(
        "banh-khot", "Bánh khọt",
        "Bánh khọt miền Nam là bánh nhỏ giòn viền, mềm bên trong, có tôm và mỡ hành, cuốn rau khi ăn.",
        "File:Bánh khọt by Baoothersks.jpg", "https://www.foodnetwork.com/recipes/food-network-kitchen/banh-khot-22957334",
        "Bột gạo;Nước cốt dừa;Nghệ;Tôm;Hành lá;Dầu ăn;Rau sống;Nước mắm",
        ["Pha bột gạo với nước cốt dừa loãng và một ít nghệ, để bột nghỉ.", "Làm sạch tôm, áp chảo sơ để tôm vừa săn.", "Làm nóng khuôn bánh khọt và cho ít dầu vào từng ô.", "Rót bột, đặt tôm lên mặt, đậy nắp đến khi bánh chín và viền giòn.", "Thêm mỡ hành, dùng bánh với rau sống và nước mắm chua ngọt."],
        region="Miền Nam", category="Bánh mặn", primary_name="Bánh Khọt", primary_publisher="Food Network Kitchen",
    ),
    dish(
        "banh-mi-cay", "Bánh mì cay",
        "Bánh mì cay Hải Phòng dùng bánh que giòn, pa-tê béo và tương ớt cay đặc trưng.",
        "File:アオサンズのバインミークエ.jpg", "https://vietnamesecookbook.com/recipes/banh-mi-cay/",
        "Bánh mì que;Pa-tê gan;Mỡ hoặc bơ;Tương ớt;Rau mùi tùy chọn",
        ["Rạch dọc bánh mì que nhưng không cắt rời hai nửa.", "Phết một lớp mỏng mỡ hoặc bơ vào mặt trong bánh.", "Dàn pa-tê đều dọc theo ổ bánh, tránh cho quá dày.", "Nướng bánh đến khi vỏ nóng giòn và nhân pa-tê dậy mùi.", "Rưới tương ớt theo khẩu vị và dùng ngay."],
        region="Hải Phòng", category="Món ăn đường phố",
    ),
    dish(
        "banh-pia", "Bánh pía",
        "Bánh pía Sóc Trăng có vỏ nhiều lớp, nhân đậu xanh sầu riêng và trứng muối.",
        "File:Bánh pía.JPG", "https://chefmundo.com/cong-thuc/banh-ngot/banh-pia/",
        "Bột mì;Dầu ăn;Đậu xanh cà vỏ;Đường;Sầu riêng;Mạch nha;Trứng muối;Trứng gà",
        ["Hấp chín đậu xanh, xay mịn rồi sên với đường, dầu, sầu riêng và mạch nha đến dẻo.", "Làm chín lòng đỏ trứng muối, chia nhân đậu và bọc mỗi lòng đỏ vào giữa.", "Nhào riêng bột nước và bột dầu, bọc hai phần bột rồi cán cuộn để tạo lớp.", "Cán vỏ, bọc kín nhân, đặt mép gấp xuống khay và xăm lỗ thoát hơi.", "Nướng bánh, lấy ra quét trứng thật mỏng rồi nướng tiếp đến khi mặt vàng."],
        region="Sóc Trăng", category="Bánh ngọt", primary_name="Công thức bánh pía", primary_publisher="ChefMundo",
    ),
    dish(
        "banh-trang-nuong", "Bánh tráng nướng",
        "Bánh tráng nướng kiểu Đà Lạt có nền bánh giòn, trứng, hành lá và các phần phủ mặn tùy chọn.",
        "File:Pizzabanhtrangnuong.JPG", "https://vietnamesecookbook.com/recipes/banh-trang-nuong/",
        "Bánh tráng;Trứng cút hoặc trứng gà;Hành lá;Tép khô;Thịt băm;Tương ớt;Mayonnaise tùy chọn",
        ["Xào chín thịt băm và chuẩn bị sẵn hành lá, tép khô cùng các phần phủ.", "Đặt bánh tráng lên bếp than hoặc chảo khô ở lửa nhỏ.", "Đập trứng lên mặt bánh, dùng thìa dàn mỏng cùng hành lá.", "Rải thịt và tép khô, xoay bánh liên tục để đáy giòn đều mà không cháy.", "Thêm tương ớt hoặc xốt tùy chọn, gập đôi hoặc để nguyên và dùng nóng."],
        region="Đà Lạt", category="Món ăn đường phố",
    ),
    dish(
        "banh-tet", "Bánh tét",
        "Bánh tét miền Nam là đòn nếp gói lá chuối với nhân đậu xanh thịt heo, nấu chín nhiều giờ.",
        "File:Banh Tet.jpg", "https://helenrecipes.com/vi/recipe-banh-tet-vietnamese-cylindrical-sticky-rice-cake-2/",
        "Gạo nếp;Đậu xanh cà vỏ;Thịt ba chỉ;Hành tím;Nước mắm;Tiêu;Lá chuối;Dây lạt",
        ["Ngâm riêng nếp và đậu xanh; nấu đậu mềm rồi nghiền, nêm nhẹ.", "Cắt thịt ba chỉ thành dải và ướp với hành, nước mắm cùng tiêu.", "Dàn đậu quanh dải thịt thành phần nhân hình trụ.", "Xếp lá chuối, dàn nếp, đặt nhân giữa rồi cuộn thành đòn và buộc chắc.", "Luộc bánh luôn ngập nước đến khi nếp chín dẻo, vớt ra rửa sạch và để ráo."],
        region="Miền Nam", category="Bánh truyền thống", primary_name="Bánh Tét", primary_publisher="Helen's Recipes",
    ),
    dish(
        "banh-xeo", "Bánh xèo",
        "Bánh xèo miền Nam có vỏ bột gạo nghệ giòn, nhân tôm thịt giá đỗ, ăn cuốn rau và chấm nước mắm.",
        "File:Bánh xèo 1.jpg", "https://vietnamesecookbook.com/recipes/banh-xeo/",
        "Bột gạo;Nước cốt dừa;Bột nghệ;Tôm;Thịt ba chỉ;Giá đỗ;Hành lá;Rau sống;Nước mắm",
        ["Pha bột gạo với nước cốt dừa loãng, nghệ và hành lá rồi để bột nghỉ.", "Xào sơ thịt ba chỉ và tôm trong chảo nóng.", "Cho ít dầu vào chảo, rót bột và nghiêng chảo để tạo lớp vỏ mỏng.", "Thêm tôm thịt và giá đỗ, đậy nắp ngắn rồi mở nắp cho vỏ giòn.", "Gập bánh, dùng ngay với rau sống và nước mắm chua ngọt."],
        region="Miền Nam", category="Bánh mặn",
    ),
    dish(
        "banh-da-cua", "Bánh đa cua",
        "Bánh đa cua Hải Phòng dùng sợi bánh đa đỏ, nước cua đồng, rau và các phần ăn kèm đặc trưng.",
        "File:Bánh đa cua Hải Phòng (27.2 (2).jpg", "https://vietnamesecookbook.com/recipes/banh-da-cua/",
        "Bánh đa đỏ;Cua đồng xay;Sườn heo;Cà chua;Rau muống;Lá lốt;Hành phi;Nước mắm",
        ["Lọc cua xay với nước nhiều lần, bỏ bã và giữ phần nước cua.", "Đun nước cua ở lửa vừa để riêu nổi thành mảng, vớt riêu ra riêng.", "Nấu nước dùng sườn, thêm cà chua xào và nước cua, nêm vừa ăn.", "Trụng bánh đa đỏ và rau muống, chia vào tô cùng riêu cua.", "Chan nước dùng, thêm lá lốt, hành phi và phần ăn kèm tùy chọn."],
        region="Hải Phòng", category="Món nước",
    ),
    dish(
        "banh-duc", "Bánh đúc",
        "Bánh đúc mặn kiểu miền Bắc có nền bột gạo mềm, dùng cùng thịt băm mộc nhĩ và nước mắm pha.",
        "File:Banhduc-northern.jpg", "https://vietnamesecookbook.com/recipes/banh-duc-tau/",
        "Bột gạo;Bột năng;Nước vôi trong thực phẩm;Thịt heo băm;Mộc nhĩ;Hành tím;Hành phi;Nước mắm",
        ["Hòa bột gạo và bột năng với nước, để lắng rồi thay phần nước trong nếu công thức nguồn yêu cầu.", "Khuấy bột trên lửa nhỏ liên tục đến khi bột đặc, bóng và chín.", "Đổ bột ra khuôn đã thoa dầu, dàn phẳng và để nguội cho định hình.", "Xào thịt băm với mộc nhĩ và hành tím, nêm vừa ăn.", "Cắt bánh thành miếng, phủ nhân, hành phi và chan nước mắm pha."],
        region="Miền Bắc", category="Bánh mặn",
    ),
    dish(
        "banh-dau-xanh", "Bánh đậu xanh",
        "Bánh đậu xanh Hải Dương là bánh ngọt khô tơi, làm từ đậu xanh đã cà vỏ, đường và chất béo.",
        "File:Bánh đậu xanh.jpg", "https://www.dienmayxanh.com/vao-bep/3-cach-lam-banh-dau-xanh-bang-noi-com-dien-dung-vi-chuan-01210",
        "Đậu xanh cà vỏ;Đường;Dầu thực vật;Nước cốt dừa tùy chọn;Vani;Muối",
        ["Ngâm đậu xanh, hấp hoặc nấu đến khi mềm rồi nghiền thật mịn.", "Cho đậu vào chảo cùng đường, dầu và một nhúm muối.", "Sên lửa nhỏ, đảo liên tục đến khi hỗn hợp khô ráo và tơi mịn.", "Thêm vani khi nhân gần đạt, trộn đều rồi để bớt nóng.", "Ép đậu vào khuôn thành miếng nhỏ, lấy ra nhẹ tay và để nguội khô."],
        region="Hải Dương", category="Bánh ngọt", primary_name="Cách làm bánh đậu xanh", primary_publisher="Điện máy XANH",
    ),
    dish(
        "bun-ca", "Bún cá",
        "Bún cá cay Hải Phòng dùng cá chiên, nước dùng cà chua thanh chua và rau ăn kèm.",
        "File:Bún Cá Hà Nội.jpg", "https://vietnamesecookbook.com/recipes/bun-ca-cay/",
        "Bún tươi;Cá;Xương cá hoặc xương heo;Cà chua;Dọc mùng;Rau cần;Hành lá;Ớt;Nước mắm",
        ["Lọc thịt cá, giữ xương để nấu nước dùng; cắt cá thành miếng và thấm khô.", "Nấu xương cá hoặc xương heo với hành để lấy nước dùng, sau đó lọc trong.", "Chiên cá đến vàng ngoài nhưng vẫn ẩm bên trong.", "Xào cà chua rồi cho vào nước dùng, nêm nước mắm và vị chua cay vừa ăn.", "Trụng bún và rau, xếp cá vào tô rồi chan nước dùng nóng."],
        region="Hải Phòng", category="Món nước",
    ),
    dish(
        "bun-mam", "Bún mắm",
        "Bún mắm miền Tây có nước dùng từ mắm cá, sả và cà tím, ăn cùng hải sản, thịt heo và rau.",
        "File:Bún mắm.jpg", "https://vietnamesecookbook.com/recipes/bun-mam/",
        "Bún tươi;Mắm cá linh hoặc cá sặc;Sả;Cà tím;Tôm;Mực;Thịt heo quay;Rau sống;Ớt",
        ["Nấu mắm cá với nước cho thịt cá tan, sau đó lọc kỹ lấy phần nước.", "Nấu nước mắm đã lọc với sả đập dập và điều chỉnh độ mặn bằng nước dùng.", "Cho cà tím vào nấu vừa mềm; luộc riêng tôm và mực để không bị dai.", "Trụng bún, xếp hải sản và thịt heo quay vào tô.", "Chan nước dùng thật nóng, dùng cùng rau sống và ớt."],
        region="Miền Tây", category="Món nước",
    ),
    dish(
        "bun-rieu", "Bún riêu",
        "Bún riêu cua dùng riêu cua đồng, cà chua và vị chua dịu trong nước dùng, ăn với rau sống.",
        "File:Bowl of Vietnamese bun rieu soup with tomato.jpg", "https://vietnamesecookbook.com/recipes/bun-rieu/",
        "Bún tươi;Cua đồng xay;Cà chua;Đậu phụ;Mắm tôm;Hành tím;Hành lá;Rau sống;Giấm bỗng hoặc me",
        ["Lọc cua xay với nước, bỏ bã và nêm rất nhẹ phần nước cua.", "Đun lửa vừa đến khi riêu nổi, vớt riêu ra để giữ thành mảng.", "Chiên vàng đậu phụ; xào cà chua với hành tím rồi cho vào nồi nước cua.", "Nêm mắm tôm và vị chua vừa ăn, thả lại riêu và đậu phụ.", "Cho bún vào tô, chan nước dùng rồi thêm hành lá và rau sống."],
        region="Miền Bắc", category="Món nước",
    ),
    dish(
        "bun-thit-nuong", "Bún thịt nướng",
        "Bún thịt nướng miền Nam gồm thịt heo ướp sả nướng, bún, rau, đồ chua, đậu phộng và nước mắm.",
        "File:Bún Thịt Nướng Chả Giò.JPG", "https://en.wikipedia.org/wiki/B%C3%BAn_th%E1%BB%8Bt_n%C6%B0%E1%BB%9Bng",
        "Bún tươi;Thịt vai heo;Sả;Tỏi;Hành tím;Nước mắm;Đường;Rau sống;Đồ chua;Đậu phộng",
        ["Thái mỏng thịt heo, ướp với sả, tỏi, hành tím, nước mắm và đường.", "Để thịt thấm rồi xiên hoặc trải lên vỉ, nướng đến khi xém cạnh và chín đều.", "Pha nước mắm chua ngọt, chuẩn bị đồ chua và rang giã đậu phộng.", "Cho rau sống và bún vào tô, xếp thịt nướng lên trên.", "Thêm đồ chua, đậu phộng và mỡ hành; chan nước mắm khi dùng."],
        region="Miền Nam", category="Món khô", primary_name="Bún thịt nướng", primary_publisher="Wikipedia contributors",
    ),
    dish(
        "bun-dau-mam-tom", "Bún đậu mắm tôm",
        "Bún đậu mắm tôm là mẹt bún lá, đậu phụ chiên, rau thơm và các phần ăn kèm dùng với mắm tôm đánh bông.",
        "File:Bún đậu mắm tôm.jpg", "https://vietnamesecookbook.com/recipes/bun-dau-mam-tom/",
        "Bún lá;Đậu phụ;Mắm tôm;Quất hoặc chanh;Đường;Dầu nóng;Rau kinh giới;Tía tô;Dưa leo",
        ["Cắt đậu phụ thành miếng vừa ăn, thấm khô rồi chiên vàng giòn các mặt.", "Cắt bún lá thành miếng và rửa sạch các loại rau ăn kèm.", "Pha mắm tôm với đường và nước quất hoặc chanh, khuấy đều.", "Rót một ít dầu chiên đang nóng vào mắm tôm và đánh đến khi nổi bọt.", "Xếp bún, đậu và rau lên mẹt; dùng ngay cùng chén mắm tôm."],
        region="Miền Bắc", category="Món khô",
    ),
    dish(
        "chao-long", "Cháo lòng",
        "Cháo lòng nấu từ gạo rang và nước luộc lòng, ăn cùng lòng heo sơ chế kỹ, hành rau và tiêu.",
        "File:Cháo lòng.jpg", "https://www.cet.edu.vn/cach-nau-chao-long-heo",
        "Gạo tẻ;Gạo nếp;Lòng heo;Xương heo;Gừng;Hành tím;Hành lá;Rau răm;Nước mắm;Tiêu",
        ["Sơ chế từng loại lòng với muối, chanh hoặc gừng, rửa kỹ và để ráo.", "Nấu xương lấy nước dùng; luộc lòng vừa chín rồi ngâm nước nguội và thái miếng.", "Rang gạo đến thơm, vo nhanh rồi cho vào nước dùng nấu lửa nhỏ.", "Khuấy định kỳ đến khi hạt gạo nở mềm, nêm nước mắm vừa ăn.", "Múc cháo ra tô, thêm lòng, hành lá, rau răm, gừng và tiêu."],
        category="Món cháo", primary_name="Cách nấu cháo lòng heo", primary_publisher="CET",
    ),
    dish(
        "ca-kho-to", "Cá kho tộ",
        "Cá kho tộ miền Nam kho cá trong nồi đất với nước màu, nước mắm và tiêu đến khi xốt sánh.",
        "File:Cá kho tộ, cá hú.jpg", "https://vietnamesecookbook.com/recipes/ca-kho-to/",
        "Cá cắt khúc;Nước mắm;Đường;Nước dừa hoặc nước;Hành tím;Tỏi;Ớt;Tiêu;Dầu ăn",
        ["Làm sạch cá, để ráo rồi ướp với nước mắm, hành, tỏi, tiêu và một phần đường.", "Thắng phần đường còn lại với ít dầu đến màu cánh gián, châm nước cẩn thận.", "Xếp cá vào nồi, thêm nước màu và nước dừa vừa gần ngập cá.", "Kho lửa vừa đến sôi rồi hạ nhỏ, trở cá nhẹ tay một lần nếu cần.", "Kho đến khi cá thấm và nước xốt sánh, thêm ớt cùng tiêu trước khi tắt bếp."],
        region="Miền Nam", category="Món kho",
    ),
    dish(
        "com-chay", "Cơm cháy",
        "Cơm cháy kiểu Ninh Bình là miếng cơm ép mỏng, phơi hoặc sấy rồi chiên giòn, dùng cùng xốt mặn.",
        "File:Cơm cháy thịt dê Ninh Bình.JPG", "https://www.thatlangon.com/cong-thuc/cach-lam-com-chay/",
        "Gạo tẻ;Gạo nếp;Dầu ăn;Nước mắm;Đường;Hành lá;Ớt;Chà bông tùy chọn",
        ["Nấu hỗn hợp gạo tẻ và một phần gạo nếp với lượng nước vừa để cơm chín dẻo.", "Ép cơm thành lớp mỏng đều trên khay, cắt miếng và sấy hoặc phơi đến khô.", "Chiên từng miếng trong dầu nóng đến khi nở giòn, vớt ra để ráo.", "Nấu nước mắm với đường thành xốt sệt nhẹ, thêm ớt và hành lá.", "Rưới xốt vừa đủ lên cơm cháy, thêm chà bông nếu dùng và thưởng thức sớm."],
        region="Ninh Bình", category="Món ăn đường phố", primary_name="Cách làm cơm cháy", primary_publisher="Thật Là Ngon",
    ),
    dish(
        "com-tam", "Cơm tấm",
        "Cơm tấm Sài Gòn dùng hạt tấm nấu chín, sườn nướng, bì, chả trứng, đồ chua và nước mắm.",
        "File:Cơm Tấm Bì Sườn Chả.jpg", "https://vietnamesecookbook.com/recipes/com-tam/",
        "Gạo tấm;Sườn cốt lết;Sả;Tỏi;Nước mắm;Đường;Bì heo;Trứng;Đồ chua;Hành lá",
        ["Vo gạo tấm nhẹ tay và nấu với lượng nước phù hợp để cơm chín tơi.", "Ướp sườn với sả, tỏi, nước mắm và đường rồi để thấm.", "Nướng sườn đến khi chín, trở đều để hai mặt xém thơm mà không khô.", "Chuẩn bị bì, chả trứng, đồ chua và mỡ hành theo phần ăn kèm.", "Xới cơm ra đĩa, xếp sườn cùng đồ ăn kèm và dùng với nước mắm chua ngọt."],
        region="Sài Gòn", category="Món cơm",
    ),
    dish(
        "hu-tieu", "Hủ tiếu",
        "Hủ tiếu Nam Vang có nước dùng xương trong, sợi hủ tiếu, thịt heo, tôm và rau giá.",
        "File:Hủ tiếu Nam Vang.jpg", "https://vietnamesecookbook.com/recipes/hu-tieu/",
        "Sợi hủ tiếu;Xương heo;Thịt nạc heo;Tôm;Thịt băm;Củ cải trắng;Hành phi;Giá;Hẹ;Nước mắm",
        ["Chần xương heo, rửa sạch rồi hầm với củ cải để lấy nước dùng trong.", "Luộc chín thịt heo và tôm trong nước dùng, vớt ra rồi thái thịt.", "Xào săn thịt băm với hành; nêm nước dùng bằng nước mắm và gia vị vừa ăn.", "Trụng nhanh sợi hủ tiếu và giá, để ráo rồi cho vào tô.", "Xếp thịt, tôm, thịt băm, hẹ và hành phi, sau đó chan nước dùng nóng."],
        region="Miền Nam", category="Món nước",
    ),
    dish(
        "mi-quang", "Mì Quảng",
        "Mì Quảng gà có sợi mì vàng, phần nhân gà đậm vị, ít nước dùng, rau sống, lạc và bánh tráng.",
        "File:Mì Quảng.jpg", "https://vietnamesecookbook.com/recipes/mi-quang/",
        "Sợi mì Quảng;Thịt gà;Nghệ;Hành tím;Nước mắm;Dầu điều;Rau sống;Đậu phộng;Bánh tráng mè",
        ["Chặt gà thành miếng, ướp với hành tím, nghệ, nước mắm và tiêu.", "Xào săn gà với dầu điều rồi thêm lượng nước vừa đủ, nấu đến khi gà mềm.", "Nêm phần nước nhân đậm đà vì món chỉ dùng một lượng nước vừa phải.", "Trụng sợi mì và chia vào tô cùng rau sống.", "Xếp gà, chan nước nhân, rắc đậu phộng và dùng với bánh tráng mè."],
        region="Quảng Nam", category="Món mì",
    ),
    dish(
        "nem-chua", "Nem chua",
        "Nem chua là thịt heo lên men cùng bì, tỏi và ớt; công thức này yêu cầu kiểm soát vệ sinh và nhiệt độ nghiêm ngặt.",
        "File:Nem chua.jpg", "https://en.wikipedia.org/wiki/Nem_chua",
        "Thịt heo nạc thật tươi;Bì heo;Tỏi;Ớt;Tiêu;Đường;Muối;Chất tạo men chuyên dụng;Lá chuối",
        ["Vệ sinh và làm lạnh dụng cụ; giữ thịt lạnh trong toàn bộ quá trình xay trộn.", "Luộc chín bì, làm sạch mỡ, thái sợi thật mảnh và để khô ráo.", "Xay thịt lạnh rồi trộn nhanh với gia vị và gói men đúng hướng dẫn của nhà sản xuất.", "Trộn bì, tỏi và tiêu; chia phần, ép chặt, thêm lát tỏi ớt rồi bọc kín.", "Ủ theo nhiệt độ và thời gian của gói men; bỏ ngay mẻ có mùi, màu hoặc cấu trúc bất thường."],
        category="Món lên men", primary_name="Nem chua", primary_publisher="Wikipedia contributors",
    ),
    dish(
        "nem-nuong", "Nem nướng",
        "Nem nướng Nha Trang là thịt heo quết dẻo nướng thơm, cuốn bánh tráng với rau và dùng cùng xốt.",
        "File:Nem nướng.jpg", "https://vietnamesecookbook.com/recipes/nem-nuong-nha-trang/",
        "Thịt heo xay;Mỡ heo;Tỏi;Hành tím;Nước mắm;Đường;Tiêu;Bánh tráng;Rau sống;Dưa leo",
        ["Giữ lạnh thịt và mỡ, trộn với tỏi, hành, nước mắm, đường và tiêu.", "Quết hỗn hợp theo một chiều đến khi dẻo kết dính, sau đó làm lạnh lại.", "Bọc thịt quanh que hoặc nặn thành miếng thuôn đều.", "Nướng trên lửa vừa, trở thường xuyên đến khi nem chín và xém thơm.", "Cuốn nem với bánh tráng, rau và dưa leo, dùng cùng xốt chấm."],
        region="Nha Trang", category="Món nướng",
    ),
    dish(
        "xoi-xeo", "Xôi xéo",
        "Xôi xéo Hà Nội gồm nếp vàng nghệ, đậu xanh nghiền thái lát và hành phi giòn.",
        "File:Xôi xéo.jpg", "https://vietnamesecookbook.com/recipes/xoi-xeo/",
        "Gạo nếp;Đậu xanh cà vỏ;Bột nghệ;Hành tím;Dầu ăn hoặc mỡ gà;Muối",
        ["Ngâm riêng nếp và đậu xanh; trộn nếp với chút nghệ và muối.", "Hấp đậu xanh đến mềm, giã hoặc xay mịn rồi nắm thành khối chắc.", "Đồ nếp đến khi hạt chín dẻo và tơi, xới nhẹ để thoát hơi.", "Thái hành tím mỏng, phi vàng giòn rồi vớt ra; giữ lại phần dầu thơm.", "Xới xôi, thái mỏng đậu xanh phủ lên trên, thêm hành phi và rưới ít dầu hành."],
        region="Hà Nội", category="Món xôi",
    ),
]


def main() -> None:
    if len(DISHES) != 30 or len({item["slug"] for item in DISHES}) != 30:
        raise RuntimeError("Catalog biên soạn phải có đúng 30 slug duy nhất")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(
        json.dumps({"dishes": DISHES}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT)


if __name__ == "__main__":
    main()
