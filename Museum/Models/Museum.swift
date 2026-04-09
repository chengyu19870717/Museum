import Foundation

struct Museum: Identifiable, Codable, Hashable {
    let id: String
    let name: String
    let englishName: String
    let city: String
    let province: String
    let category: MuseumCategory
    let founded: Int?
    let area: Double?           // 建筑面积，平方米
    let annualVisitors: Int?    // 年参观人次
    let freeEntry: Bool
    let address: String
    let website: String?
    let phone: String?
    let openingHours: String
    let summary: String
    let highlights: [String]    // 镇馆之宝 / 亮点
    let images: [MuseumImage]
    let latitude: Double?
    let longitude: Double?
    let grade: MuseumGrade?     // 国家等级

    var localDirectory: String { id }
}

struct MuseumImage: Codable, Hashable {
    let filename: String
    let caption: String
    let credit: String?
    let license: String?
}

enum MuseumCategory: String, Codable, CaseIterable {
    case history        = "历史"
    case art            = "艺术"
    case science        = "科技"
    case natural        = "自然"
    case military       = "军事"
    case revolutionary  = "革命纪念"
    case folk           = "民俗"
    case specialty      = "专题"
    case comprehensive  = "综合"
}

enum MuseumGrade: String, Codable {
    case nationalFirst  = "国家一级博物馆"
    case nationalSecond = "国家二级博物馆"
    case nationalThird  = "国家三级博物馆"
}
