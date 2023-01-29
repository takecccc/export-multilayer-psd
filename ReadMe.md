# What is this?
SubstancePainter用のマルチレイヤーpsdのエクスポートプラグインです。
最低限、自分の環境で目的の動作を実現するように作っているだけなので、動かない環境もあるかもしれません。

# 動作確認環境
- Windows 10
- Substance Painter 8.3.0 build 2094
- CLIP STUDIO PAINT PRO(64bit) Version 1.12.3 202206201552

# How to Install
1. pythonプラグインフォルダを開く
   `Menu > Python > プラグインフォルダフォルダー`で開けます。
   特に設定を変えていなければ、`%userprofile%\Documents\Adobe\Adobe Substance 3D Painter\python\plugins\`のはず。
2. 解凍済みのこのフォルダをpythonプラグインフォルダに配置
3. setup.batを実行して、依存するpythonモジュールをインストール

# How to Use
1. テクスチャをエクスポートしたいプロジェクトを開く。
2. `Menu > ファイル > export as multilayer psd` が追加されているので、実行。
3. 各マテリアルについて、エクスポートするチャネルを選択。
4. エクスポートするパス、テクスチャサイズ、パディング方法、拡張幅、ビット深度を選択。
5. OKをクリック。
6. 指定したフォルダに各レイヤーの画像と共にpsdファイルがエクスポートされます。