class Ingredient {
  const Ingredient({required this.name, this.quantity, this.unit});
  final String name;
  final String? quantity;
  final String? unit;

  factory Ingredient.fromJson(Map<String, dynamic> json) => Ingredient(
    name: json['name'] as String? ?? '',
    quantity: json['quantity'] as String?,
    unit: json['unit'] as String?,
  );
}

class RecipeReference {
  const RecipeReference({
    required this.name,
    required this.url,
    required this.publisher,
    required this.accessedAt,
  });

  final String name;
  final String url;
  final String publisher;
  final String accessedAt;

  factory RecipeReference.fromJson(Map<String, dynamic> json) =>
      RecipeReference(
        name: json['name'] as String? ?? '',
        url: json['url'] as String? ?? '',
        publisher: json['publisher'] as String? ?? '',
        accessedAt: json['accessedAt'] as String? ?? '',
      );
}

class RecipeData {
  const RecipeData({
    required this.ingredients,
    required this.steps,
    required this.sourceUrl,
    required this.sourceName,
    required this.sourceRevisionUrl,
    required this.licenseName,
    required this.licenseUrl,
    required this.attribution,
    required this.modifiedFromSource,
    required this.contentOrigin,
    required this.verificationStatus,
    required this.verificationNote,
    required this.references,
  });
  final List<Ingredient> ingredients;
  final List<String> steps;
  final String sourceUrl;
  final String sourceName;
  final String sourceRevisionUrl;
  final String licenseName;
  final String licenseUrl;
  final String attribution;
  final bool modifiedFromSource;
  final String contentOrigin;
  final String verificationStatus;
  final String verificationNote;
  final List<RecipeReference> references;

  factory RecipeData.fromJson(Map<String, dynamic> json) => RecipeData(
    ingredients: (json['ingredients'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(Ingredient.fromJson)
        .toList(growable: false),
    steps: (json['steps'] as List<dynamic>? ?? const [])
        .map((item) => item.toString())
        .toList(growable: false),
    sourceUrl: json['sourceUrl'] as String? ?? '',
    sourceName: json['sourceName'] as String? ?? '',
    sourceRevisionUrl: json['sourceRevisionUrl'] as String? ?? '',
    licenseName: json['licenseName'] as String? ?? '',
    licenseUrl: json['licenseUrl'] as String? ?? '',
    attribution: json['attribution'] as String? ?? '',
    modifiedFromSource: json['modifiedFromSource'] as bool? ?? false,
    contentOrigin: json['contentOrigin'] as String? ?? '',
    verificationStatus: json['verificationStatus'] as String? ?? '',
    verificationNote: json['verificationNote'] as String? ?? '',
    references: (json['references'] as List<dynamic>? ?? const [])
        .whereType<Map<String, dynamic>>()
        .map(RecipeReference.fromJson)
        .toList(growable: false),
  );
}

class Dish {
  const Dish({
    required this.id,
    required this.slug,
    required this.name,
    required this.hasRecipe,
    required this.isFavorite,
    this.aliases = const [],
    this.region,
    this.category,
    this.prepMinutes,
    this.cookMinutes,
    this.explicitTotalMinutes,
    this.difficulty,
    this.servings,
    this.servingsText,
    this.description,
    this.imageUrl,
    this.imageAttribution,
    this.imageAuthor,
    this.imageSourceUrl,
    this.imageLicenseName,
    this.imageLicenseUrl,
    this.recipe,
    this.recipeMessage,
  });

  final int id;
  final String slug;
  final String name;
  final List<String> aliases;
  final String? region;
  final String? category;
  final int? prepMinutes;
  final int? cookMinutes;
  final int? explicitTotalMinutes;
  final String? difficulty;
  final int? servings;
  final String? servingsText;
  final String? description;
  final String? imageUrl;
  final String? imageAttribution;
  final String? imageAuthor;
  final String? imageSourceUrl;
  final String? imageLicenseName;
  final String? imageLicenseUrl;
  final bool hasRecipe;
  final bool isFavorite;
  final RecipeData? recipe;
  final String? recipeMessage;

  int? get totalMinutes =>
      explicitTotalMinutes ??
      (prepMinutes == null && cookMinutes == null
          ? null
          : (prepMinutes ?? 0) + (cookMinutes ?? 0));

  Dish copyWith({bool? isFavorite}) => Dish(
    id: id,
    slug: slug,
    name: name,
    aliases: aliases,
    region: region,
    category: category,
    prepMinutes: prepMinutes,
    cookMinutes: cookMinutes,
    explicitTotalMinutes: explicitTotalMinutes,
    difficulty: difficulty,
    servings: servings,
    servingsText: servingsText,
    description: description,
    imageUrl: imageUrl,
    imageAttribution: imageAttribution,
    imageAuthor: imageAuthor,
    imageSourceUrl: imageSourceUrl,
    imageLicenseName: imageLicenseName,
    imageLicenseUrl: imageLicenseUrl,
    hasRecipe: hasRecipe,
    isFavorite: isFavorite ?? this.isFavorite,
    recipe: recipe,
    recipeMessage: recipeMessage,
  );

  factory Dish.fromJson(Map<String, dynamic> json) {
    final rawRecipe = json['recipe'];
    return Dish(
      id: json['id'] as int? ?? 0,
      slug: json['slug'] as String? ?? '',
      name: json['name'] as String? ?? 'Không xác định',
      aliases: (json['aliases'] as List<dynamic>? ?? const [])
          .map((item) => item.toString())
          .toList(growable: false),
      region: json['region'] as String?,
      category: json['category'] as String?,
      prepMinutes: json['prepMinutes'] as int?,
      cookMinutes: json['cookMinutes'] as int?,
      explicitTotalMinutes: json['totalMinutes'] as int?,
      difficulty: json['difficulty'] as String?,
      servings: json['servings'] as int?,
      servingsText: json['servingsText'] as String?,
      description: json['description'] as String?,
      imageUrl: json['imageUrl'] as String?,
      imageAttribution: json['imageAttribution'] as String?,
      imageAuthor: json['imageAuthor'] as String?,
      imageSourceUrl: json['imageSourceUrl'] as String?,
      imageLicenseName: json['imageLicenseName'] as String?,
      imageLicenseUrl: json['imageLicenseUrl'] as String?,
      hasRecipe: json['hasRecipe'] as bool? ?? false,
      isFavorite: json['isFavorite'] as bool? ?? false,
      recipe: rawRecipe is Map<String, dynamic>
          ? RecipeData.fromJson(rawRecipe)
          : null,
      recipeMessage: json['recipeMessage'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
    'id': id,
    'slug': slug,
    'name': name,
    'aliases': aliases,
    'region': region,
    'category': category,
    'prepMinutes': prepMinutes,
    'cookMinutes': cookMinutes,
    'totalMinutes': explicitTotalMinutes,
    'difficulty': difficulty,
    'servings': servings,
    'servingsText': servingsText,
    'description': description,
    'imageUrl': imageUrl,
    'imageAttribution': imageAttribution,
    'imageAuthor': imageAuthor,
    'imageSourceUrl': imageSourceUrl,
    'imageLicenseName': imageLicenseName,
    'imageLicenseUrl': imageLicenseUrl,
    'hasRecipe': hasRecipe,
    'isFavorite': isFavorite,
  };
}
