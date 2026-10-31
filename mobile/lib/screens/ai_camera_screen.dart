import 'dart:typed_data';

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';

import '../services/ai_service.dart';
import '../state/app_state.dart';
import '../theme/app_theme.dart';
import 'ai_result_screen.dart';

class AiCameraScreen extends StatefulWidget {
  const AiCameraScreen({super.key});

  @override
  State<AiCameraScreen> createState() => _AiCameraScreenState();
}

class _AiCameraScreenState extends State<AiCameraScreen> {
  final _picker = ImagePicker();
  XFile? _image;
  Uint8List? _preview;
  bool _loading = false;

  Future<void> _pick(ImageSource source) async {
    try {
      final image = await _picker.pickImage(
        source: source,
        imageQuality: 92,
        maxWidth: 1800,
      );
      if (image == null) return;
      final bytes = await image.readAsBytes();
      if (!mounted) return;
      setState(() {
        _image = image;
        _preview = bytes;
      });
    } catch (_) {
      _message(
        'Không thể mở ${source == ImageSource.camera ? 'camera' : 'thư viện ảnh'}. Hãy kiểm tra quyền truy cập.',
      );
    }
  }

  Future<void> _analyze() async {
    final image = _image;
    final preview = _preview;
    if (image == null || preview == null) {
      _message('Hãy chụp hoặc chọn một ảnh món ăn trước.');
      return;
    }
    setState(() => _loading = true);
    try {
      final result = await AiService(AppStateScope.of(context).api)
          .predict(image);
      if (!mounted) return;
      await Navigator.of(context).push(
        MaterialPageRoute(
          builder: (_) => AiResultScreen(imageBytes: preview, result: result),
        ),
      );
    } on AiServiceException catch (error) {
      _message(error.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _message(String text) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(text), behavior: SnackBarBehavior.floating),
    );
  }

  @override
  Widget build(BuildContext context) {
    return ColoredBox(
      color: const Color(0xFF131715),
      child: SafeArea(
        child: Padding(
          padding: const EdgeInsets.fromLTRB(18, 18, 18, 22),
          child: Column(
            children: [
              Row(
                children: [
                  const Expanded(
                    child: Column(
                      children: [
                        Text(
                          'Nhận diện món ăn bằng AI',
                          style: TextStyle(
                            color: Colors.white,
                            fontSize: 17,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        SizedBox(height: 4),
                        Text(
                          'Chụp ảnh món ăn để tìm tên món',
                          style: TextStyle(color: Colors.white60, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                  Tooltip(
                    message: 'Ảnh chỉ được gửi để nhận diện và không được lưu.',
                    child: const Icon(
                      Icons.privacy_tip_outlined,
                      color: Colors.white70,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              Expanded(
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(28),
                  child: Stack(
                    fit: StackFit.expand,
                    children: [
                      if (_preview != null)
                        Image.memory(_preview!, fit: BoxFit.cover)
                      else
                        const ColoredBox(
                          color: Color(0xFF202723),
                          child: Center(
                            child: Icon(
                              Icons.restaurant_menu_rounded,
                              size: 92,
                              color: Colors.white24,
                            ),
                          ),
                        ),
                      DecoratedBox(
                        decoration: BoxDecoration(
                          border: Border.all(color: AppColors.leaf, width: 3),
                          borderRadius: BorderRadius.circular(28),
                        ),
                      ),
                      if (_preview == null)
                        const Center(
                          child: DecoratedBox(
                            decoration: BoxDecoration(
                              color: Color(0xB317201A),
                              borderRadius: BorderRadius.all(
                                Radius.circular(18),
                              ),
                            ),
                            child: Padding(
                              padding: EdgeInsets.symmetric(
                                horizontal: 18,
                                vertical: 12,
                              ),
                              child: Text(
                                'Đặt món ăn vào giữa khung hình',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 22),
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceAround,
                children: [
                  _Action(
                    icon: Icons.photo_library_outlined,
                    label: 'Thư viện',
                    onTap: () => _pick(ImageSource.gallery),
                  ),
                  GestureDetector(
                    onTap: () => _pick(ImageSource.camera),
                    child: Container(
                      width: 82,
                      height: 82,
                      padding: const EdgeInsets.all(6),
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        border: Border.all(color: AppColors.leaf, width: 4),
                      ),
                      child: Container(
                        decoration: const BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.circle,
                        ),
                      ),
                    ),
                  ),
                  _Action(
                    icon: Icons.cameraswitch_outlined,
                    label: 'Đổi camera',
                    onTap: () => _pick(ImageSource.camera),
                  ),
                ],
              ),
              const SizedBox(height: 18),
              SizedBox(
                width: double.infinity,
                child: FilledButton.icon(
                  onPressed: _loading ? null : _analyze,
                  icon: _loading
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.auto_awesome_rounded),
                  label: Text(
                    _loading ? 'AI đang nhận diện...' : 'Nhận diện bằng AI',
                  ),
                  style: FilledButton.styleFrom(
                    backgroundColor: AppColors.forest,
                    padding: const EdgeInsets.symmetric(vertical: 16),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _Action extends StatelessWidget {
  const _Action({required this.icon, required this.label, required this.onTap});
  final IconData icon;
  final String label;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => InkWell(
    onTap: onTap,
    borderRadius: BorderRadius.circular(18),
    child: Padding(
      padding: const EdgeInsets.all(10),
      child: Column(
        children: [
          Icon(icon, color: Colors.white, size: 28),
          const SizedBox(height: 5),
          Text(
            label,
            style: const TextStyle(color: Colors.white70, fontSize: 11),
          ),
        ],
      ),
    ),
  );
}
